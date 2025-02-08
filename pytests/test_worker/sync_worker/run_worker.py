from hepai import HRModel

class CustomWorkerModel(HRModel):  # Define a custom worker model inheriting from HRModel.
    def __init__(self, name: str = "hepai/custom-model", **kwargs):
        super().__init__(name=name, **kwargs)

    @HRModel.remote_callable  # Decorate the function to enable remote call.
    def custom_method(self, a: int = 1, b: int = 2) -> int:
        """Define your custom method here."""
        return a + b

if __name__ == "__main__":
    CustomWorkerModel.run()  # Run the custom worker model.