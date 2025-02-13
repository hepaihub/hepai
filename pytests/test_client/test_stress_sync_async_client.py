import os
import asyncio
import time
import logging
import random
from hepai import HepAI, AsyncHepAI
from collections import defaultdict
from argparse import ArgumentParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stress_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StressTester:
    def __init__(
            self,
            base_url,
            api_key,
            model,
            interval=0,
            random_interval=False,
            use_async=False
    ):
        self.use_async = use_async
        if self.use_async:
            self.client = AsyncHepAI(base_url=base_url, api_key=api_key)
        else:
            self.client = HepAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.stats = {
            'durations': [],
            'status_counts': defaultdict(int),
            'token_counts': [],
            'time_to_first_token': [],
            'tokens_per_sec': []
        }
        self.lock = asyncio.Lock()
        self.interval = interval
        self.random_interval = random_interval

    def _make_request_sync(self, request_data):
        """同步阻塞请求"""
        start_time = time.perf_counter()
        status = "success"
        first_token_time = None
        token_count = 0

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": request_data}],
                stream=True,
                temperature=1E-6,
            )
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    token_count += 1
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
        except Exception as e:
            status = f"error: {str(e)}"
            logger.error(f"Sync request failed: {e}")
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            time_to_first_token = first_token_time - start_time if first_token_time else duration
            generation_duration = end_time - first_token_time if first_token_time else 0
            tokens_per_sec = token_count / generation_duration if generation_duration > 0 else 0

        return (duration, status, token_count, time_to_first_token, tokens_per_sec)

    async def _make_request_async(self, request_data):
        """异步非阻塞请求"""
        start_time = time.perf_counter()
        status = "success"
        first_token_time = None
        token_count = 0

        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": request_data}],
                stream=True
            )
            async for chunk in completion:
                if chunk.choices[0].delta.content:
                    token_count += 1
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
        except Exception as e:
            status = f"error: {str(e)}"
            logger.error(f"Async request failed: {e}")
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            time_to_first_token = first_token_time - start_time if first_token_time else None
            generation_duration = end_time - first_token_time if first_token_time else 0
            tokens_per_sec = token_count / generation_duration if generation_duration > 0 else 0

        return (duration, status, token_count, time_to_first_token, tokens_per_sec)

    async def _record_metrics(self, duration, status, token_count, time_to_first_token, tokens_per_sec):
        async with self.lock:
            self.stats['durations'].append(duration)
            self.stats['status_counts'][status] += 1
            self.stats['token_counts'].append(token_count)
            self.stats['time_to_first_token'].append(time_to_first_token)
            self.stats['tokens_per_sec'].append(tokens_per_sec)

    async def _make_request(self, request_data):
        """统一的请求处理入口"""
        if self.use_async:
            result = await self._make_request_async(request_data)
        else:
            result = await asyncio.to_thread(self._make_request_sync, request_data)
        
        await self._record_metrics(*result)
        return result[0]

    async def worker(self, request_queue, sem):
        """处理请求的工作协程"""
        while True:
            try:
                async with sem:
                    # 间隔控制逻辑
                    if self.interval > 0:
                        wait_time = random.uniform(0, self.interval) if self.random_interval else self.interval
                        await asyncio.sleep(wait_time)

                    request_data = await request_queue.get()
                    await self._make_request(request_data)
                    request_queue.task_done()

            except asyncio.CancelledError:
                break

    async def run_test(self, concurrency, total_requests, request_data):
        """执行压力测试"""
        request_queue = asyncio.Queue()
        sem = asyncio.Semaphore(concurrency)

        # 填充请求队列
        for _ in range(total_requests):
            await request_queue.put(request_data)

        # 创建工作协程
        workers = [asyncio.create_task(self.worker(request_queue, sem))
                   for _ in range(concurrency)]

        start_time = time.time()
        await request_queue.join()
        total_duration = time.time() - start_time

        # 清理工作协程
        for worker in workers:
            worker.cancel()

        # 生成测试报告
        successful = self.stats['status_counts'].get('success', 0)
        errors = total_requests - successful
        avg_duration = sum(self.stats['durations']) / len(self.stats['durations']) if self.stats['durations'] else 0
        avg_time_to_first_token = sum(self.stats['time_to_first_token']) / len(self.stats['time_to_first_token']) if self.stats['time_to_first_token'] else 0
        avg_tokens_per_sec = sum(self.stats['tokens_per_sec']) / len(self.stats['tokens_per_sec']) if self.stats['tokens_per_sec'] else 0
        qps = successful / total_duration if total_duration > 0 else 0

        report = (
            f"\n=== Test Summary ===\n"
            f"Concurrency Level: {concurrency}\n"
            f"Total Requests: {total_requests}\n"
            f"Successful: {successful}\n"
            f"Errors: {errors}\n"
            f"Average Latency: {avg_duration:.4f}s\n"
            f"Avg Time to First Token: {avg_time_to_first_token:.4f}s\n"
            f"Avg Tokens per Second: {avg_tokens_per_sec:.2f}\n"
            f"QPS: {qps:.2f}\n"
            f"Total Duration: {total_duration:.2f}s\n"
            f"Mode: {'Async' if self.use_async else 'Sync'}\n"
        )
        logger.info(report)
        return self.stats

async def main():
    parser = ArgumentParser()
    parser.add_argument('--concurrency', type=int, default=10, help='并发用户数')
    parser.add_argument('--requests', type=int, default=10, help='总请求数')
    # parser.add_argument('--model', type=str, default='openai/gpt-4o-mini', help='模型名称')
    parser.add_argument('--model', type=str, default='deepseek-ai/DeepSeek-R1-Distill-Qwen-32B-with-reasoning', help='模型名称')
    parser.add_argument('--interval', type=float, default=0, help='请求间隔（秒）')
    parser.add_argument('--random-interval', action='store_true', help='启用随机间隔')
    parser.add_argument('--async', dest='use_async', action='store_true', help='使用异步模式')
    args = parser.parse_args()

    tester = StressTester(
        base_url="https://aiapi001.ihep.ac.cn/apiv2",
        # base_url="http://localhost:42601/apiv2",
        # base_url="http://aiapi.ihep.ac.cn/v1",
        # api_key=os.environ.get('HEPAI_API_KEY2'),
        api_key=os.getenv("DDF_ZDZHANG_API_KEY"),
        # api_key=os.getenv("HEPAI_API_KEY"),
        model=args.model,
        interval=args.interval,
        random_interval=args.random_interval,
        use_async=args.use_async
    )

    question = "hi"
    question = "Explain the theory of relativity"


    await tester.run_test(
        concurrency=args.concurrency,
        total_requests=args.requests,
        request_data=question,
    )

if __name__ == "__main__":
    asyncio.run(main())