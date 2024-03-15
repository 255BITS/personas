# ML Inference Pipeline

ML Inference Pipeline is a Python library that provides a flexible and intuitive way to build and execute machine learning inference pipelines(DAGs). It allows you to define tasks, compose them into pipelines, and execute them efficiently using asynchronous programming.

## Features

- Define tasks as simple Python functions or coroutines
- Compose tasks into pipelines using intuitive operators (`>>` for sequential composition, `|` for parallel composition)
- Execute pipelines asynchronously using `asyncio`
- Built-in support for setting and retrieving task outputs
- Validation of pipeline structure to ensure proper usage of `set_output` and `get_output`
- Extensible architecture to accommodate custom task types and behaviors

## Installation

You can install ML Inference Pipeline using pip:

```
pip install ml-inference-pipeline
```

## Usage

Here's a simple example of how to use ML Inference Pipeline:

```python
from ml_inference_pipeline import task, Pipeline

@task
async def task1(x):
    return x * 2

@task
async def task2(x):
    return x + 1

@task
async def task3(x, y):
    return x + y

pipeline = Pipeline(
    (task1 | task2) >> task3
)

result = await pipeline(5)
print(result)  # Output: 21
```

## Documentation

For detailed documentation and more examples, please refer to the [ML Inference Pipeline Documentation](link-to-documentation).

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](link-to-repository).

## License

ML Inference Pipeline is released under the [MIT License](link-to-license).

## Acknowledgements

We would like to thank the open-source community for their valuable contributions and inspiration.

