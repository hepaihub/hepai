# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# This script is used to collect all events for streaming #
# Author: Zhengde Zhang                                   #
# Date: 2024-05-23                                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from typing import List, Callable, Generator
import asyncio
import queue
import time
import threading

class EventCollector:
    """
    支持运行时的事件收集
    Usage:
        evc = EventCollector()
        evc.add_event_source(Callable)
        stream = evc.run()
        for x in stream:
            print(f"Event: {x}")
    """
    def __init__(self):
        self.que = queue.Queue()
        self.event_sources: List[Callable] = []

    def add_event_source(self, event_source: Generator):
        """添加一个事件源，该事件源应该是一个生成器"""
        self.event_sources.append(event_source)
    
    def producer(self, gen, q):
        for item in gen:  # 生成器
            q.put(item)
        q.put(None)  # 自动的停止标志

    def consumer(self, q: queue.Queue, max_producers):
        count = 0  # source完成的标志
        while True:
            item = q.get()
            if item is None:
                count += 1
                if count == max_producers:
                    break
            else:
                yield item
            q.task_done()

    def all_events_generator(self):
        """返回流式所有的事件源信息，事件源停止后，不再返回事件"""
        evss = self.event_sources
        
        # res = await asyncio.gather(*evss)
        producers = [
            threading.Thread(target=self.producer, args=(gen, self.que))
            for gen in evss
        ]
        # consumer_thread = threading.Thread(target=self.consumer, args=(self.que, len(producers)))
        consumer = self.consumer(self.que, len(producers))
        
        for p in producers:
            p.start()
        
        # consumer_thread.start()
        return consumer
    
        # 等待所有的生产者结束
        for p in producers:
            p.join()
        # 等待消费者结束
        # consumer_thread.join()

class FakeEventSource_1():
    # async def __anext__(self):
    def event_generator(self):
        # print("FakeEventSource_1")
        # await asyncio.sleep(1)
        for i in range(2):
            time.sleep(1)
            yield {
                "data": "data",
                "event": f"fe1_data_{i}",
            }

class FakeEventSource_2():
    # async def __anext__(self):
    def event_generator(self):
        # print("FakeEventSource_2")
        # await asyncio.sleep(1)
        for i in range(2):
            time.sleep(2)
            yield {
                "data": "data",
                "event": f"fe2_data_{i}",
            }

class FakeEventSource_3():

    def __init__(self) -> None:
        self.fe3_msg = "in1"
    # async def __anext__(self):

    
    def run_chat(self, evc: EventCollector):
        msg = ""
        msg += self.fe3_msg
        for i in range(3):
            round = i+1
            gen = self.gen_reply(msg, round)
            evc.add_event_source(gen)

        pass

    def gen_reply(self, msg, round):
        # print("FakeEventSource_3")
        # await asyncio.sleep(1)
        outputs = [f'{msg}-r{round}-c1', f'{msg}-r{round}-c2']
        full_response = ""
        for i, x in enumerate(outputs):
            time.sleep(1)
            full_response += x
            self.fe3_msg = x
            yield {
                "data": x,
                "event": f"fe3.round{round}.chunk{i}",
            }
        msg += full_response
        
    async def a_run_chat(self, evc: EventCollector):
        msg = "in1"
        for i in range(2):
            round = i+1
            res = await self.gen_reply(msg, round)
            pass


def test():
    evc = EventCollector()
    # evc.add_event_source(FakeEventSource_1().event_generator())
    # evc.add_event_source(FakeEventSource_2().event_generator())
    # stream = asyncio.run(evc.all_events_generator())
    fe3 = FakeEventSource_3()
    # fe3.run_chat(evc=evc)
    fe3.a_run_chat(evc=evc)

    stream = evc.all_events_generator()
    for x in stream:
        print(f"Event: {x}")

async def test():
    env = EventCollector()
    fe3 = FakeEventSource_3()
    await fe3.a_run_chat(env)

    return env.all_events_generator()
        
                
if __name__ == '__main__':
    # test()
    import asyncio
    stream = asyncio.run(test())
    for x in stream:
        print(f"Event: {x}")
