---
title: Sample Document
author: Test Author
date: 2026-01-01
---

# Introduction

This is the introduction section with some **bold** and *italic* text.

## Getting Started

Follow these steps to get started:

- Step 1: Install the package
- Step 2: Configure settings
  - Sub-step A: Edit config file
  - Sub-step B: Set environment variables
- Step 3: Run the application

### Prerequisites

You need Python 3.10 or later.

## Usage

```python
from jostack_mdparse import extract

result = extract("README.md", format="json")
print(result)
```

Here is some <strong>inline HTML</strong> content.

## Links

See [Installation Guide](./docs/install.md) for more details.
Visit [GitHub](https://github.com/hyunhee-jo/jostack-mdparse) for the source code.

## Conclusion

That's all for now.
