# Simulator-CPI

This project is a backend service for a simulator application based on [this paper](https://doi.org/10.48550/arXiv.2410.22760). It provides an API to
manage and execute BPMN+CPI models through Petri Nets.

# Table of Contents

1. [Installation](#installation)  
   1. [Prerequisites](#prerequisites)  
   2. [Using Docker](#using-docker)  
   3. [Using Python](#using-python)  
2. [API Documentation](#api-documentation)  
3. [Endpoints](#endpoints)  
4. [API Workflow](#api-workflow)  
5. [Project Structure](#project-structure)  
6. [Models](#models)  
   1. [BPMN Structure](#bpmn-structureregion-models)  
       - [Task](#task)  
       - [Nature](#nature)  
       - [Choice](#choice)  
       - [Parallel](#parallel)  
       - [Loop](#loop)  
       - [Sequential](#sequential)  
   2. [Petri Net Structure](#petri-net-structure)  
       - [Place Structure](#place-structure)  
       - [Transition Structure](#transition-structure)  
       - [Arc Structure](#arc-structure)  
       - [Petri Net Wrapper](#petri-net-wrapper)  
   3. [Execution Tree Structure](#execution-tree-structure)  
   4. [Strategy Structure](#strategy-structure)  
       - [Create New Strategy](#create-new-strategy)  
7. [Logging](#logging)  
8. [Authors](#authors)

## Installation

### Prerequisites

* Install dependencies:

```bash
pip install -r requirements.txt
```

or create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

* Create .env or docker.env(if you want to use docker) file in the root directory with the following content:

```dotenv
SIMULATOR_API_HOST=<your_host>
SIMULATOR_API_PORT=<your_port>
SIMULATOR_API_TITLE=<your_api_title>
SIMULATOR_API_VERSION=<your_api_version>
SIMULATOR_API_DOCS_URL=<your_docs_url>
```

### Using Docker

```bash
docker build -t <tag> .
docker run -p <port>:<port> <tag>
```

### Using Python

Avoid using `uvicorn` or `fastapi` directly to run the application, as it may lead to issues with relative imports.
Instead, use the following command to run the application:

```bash
python3 src/main.py
```

The API will be available at `http://<your_host>:<your_port>`.

## API Documentation

Once the server is running, you can access the interactive API documentation at:

```
http://<your_host>:<your_port>/<your_docs_url>
```

Replace `<your_host>`, `<your_port>`, and `<your_docs_url>` with the values you set in the `.env` file.

## Endpoints

The API provides the following endpoints:

* `POST /execute`: Execute a simulation with the provided parameters. In src/model/endpoints you can find all models and
  method to convert request and response. Accept two types of input:
    * You can pass only BPMN parse tree, and it will create petri net, execution tree and return all of them.
    * You can pass BPMN parse tree, petri net, execution tree and transitions to execute the simulation and return same
      BPMN, same petri net and execution tree with a possible new node.

## API Workflow

1. **Input**: The user sends a POST request to the `/execute` endpoint with one of JSON payload defined above.
2. **Processing**: The server creates a NetContext object, that contains the data sent to the server and also define the
   execution strategy.
3. **Execution**: The server executes the simulation based on the provided data and strategy.
4. **Output**: The server returns a JSON response containing the results of the simulation, including the BPMN parse
   tree, petri net, and execution tree.

## Project Structure

* `src/`: Contains the source code for the FastAPI application.
    * `main.py`: The main entry point for the FastAPI application.
    * `converter/`: Contains the conversion methods for a model.
    * `models/`: Contains the data models used in the application.
        * `endpoints/`: Contains the Pydantic models for request and response validation.
    * `strategy/`: Contains the business logic to execute simulations.
    * `utils/`: Contains utility functions and classes.
* `tests/`: Contains unit tests for the application.
* `Dockerfile`: Docker configuration file for building the application image.
* `requirements.txt`: List of Python dependencies.
* `.env`: Environment variables for configuration (not included in the repository).

# Models

Let's describe the structure of the main models used in this project.

## BPMN Structure/Region Models

BPMN package contains all the classes to represent a BPMN diagram as a parse tree.
Parse tree have 6 types of nodes(also called regions):

* **Task**: represents a task in the BPMN diagram.
* **Nature**: represents a nature in the BPMN diagram.
* **Choice**: represents a choice in the BPMN diagram.
* **Parallel**: represents a parallel in the BPMN diagram.
* **Loop**: represents a loop in the BPMN diagram.
* **Sequential**: a sequential aggregation of regions.
  We use only one class called `RegionModel` to represents BPMN parse tree.
  Below there's attributes description for each parse node type(also called region):

### TASK

* `id`: unique identifier of the task.
* `label`: label of the task.
* `type`: type of the region, in this case "task".
* `impacts`: list of impacts of the task.
* `duration`: duration of the task.

### NATURE

* `id`: unique identifier of the nature.
* `label`: label of the nature.
* `type`: type of the region, in this case "nature".
* `children`: list of child regions.
* `distribution`: list of probabilities related to its children.

### CHOICE

* `id`: unique identifier of the choice.
* `label`: label of the choice.
* `type`: type of the region, in this case "choice".
* `children`: list of child regions.

### PARALLEL

* `id`: unique identifier of the parallel.
* `label`: label of the parallel.
* `type`: type of the region, in this case "parallel".
* `children`: list of child regions.

### LOOP

* `id`: unique identifier of the loop.
* `label`: label of the loop.
* `type`: type of the region, in this case "loop".
* `children`: a list containing only one child.
* `distribution`: a float representing the probability to re-execute the loop.
* `bound`: an integer representing the maximum number of iterations of the loop.

### SEQUENTIAL

* `id`: unique identifier of the sequential.
* `label`: label of the sequential.
* `type`: type of the region, in this case "sequential".
* `children`: list of child regions.

## Petri Net Structure

Petri Net package contains all wrapper classes of pm4py.

### Place Structure

A place contains all method of pm4py Place class and also has some additional attributes to access easier in properties
dictionary of pm4py Place class.

* region_label: label of the region that generated this place.
* region_type: type of the region that generated this place.
* entry_id: id of the region that generated this place.
* exit_id: id of the region that generated this place.
* impacts: list of impacts of the region that generated this place.
* duration: duration of the region that generated this place.
* visit_limit: maximum number of visits of this place. Used to limit the number of visits in loops.

### Transition Structure

A transition contains all method of pm4py Transition class and also has some additional attributes to access easier in
properties dictionary of pm4py Transition class.

* region_label: label of the region that generated this transition.
* region_type: type of the region that generated this transition.
* region_id: id of the region that generated this transition.
* probability: probability of this transition. Used in nature regions.
* stop: boolean value indicating whether this transition is a stop transition, representing a point where the user can
  choose which path to execute next.

### Arc Structure

An arc contains all method of pm4py Arc class.

### Petri Net Wrapper

Petri net wrapper doesn't add any additional attributes but overrides `__eq__`with a more suitable implementation for
our use case.

## Execution Tree Structure

Execution tree is based on anytree package.
It contains:

* `root`: root of the execution tree.
* `current_node`: current node of the execution tree.'

Each node contains:

* `id`: unique identifier of the node.
* `name`: name of the node.
* `parent`: parent of the node.
* `children`: list of children of the node.
* `snapshot`: snapshot of the execution at this node.
    * `marking`: current marking of the petri net at this node.
    * `probability`: probability of reaching this node.
    * `impacts`: cumulative impacts of the execution up to this node.
    * `execution_time`: cumulative execution time of the execution up to this node.

And also contains some methods listed below:

* `add_snapshot`: add a snapshot to the current node.
* `find_nodes_by_marking`: find all nodes that matches the marking.
* `get_node_by_id`: get a node by its id.
* `from_context`: **_static method_** to create an execution tree from a NetContext object.

## Strategy Structure

Strategy package is a sort of strategy pattern implementation. It contains all the business logic to execute a
simulation.
Every class contains two methods:

* `saturate`: it takes NetContext object and current marking/state of the petri net. Execute every transition until it
  reaches a transition with stop.
* `consume`: it takes NetContext object, current marking/state of the petri net and a list of transitions(choices) to
  execute. Call saturate, execute those choices and recall saturate.

### Create new Strategy

To create a new strategy for executing simulations, follow these steps:

1. Create a new class in the `src/strategy/` directory that follows the `StrategyProto` class rules.
2. Implement the required methods for your strategy.
3. **Remember to not use it directly but use it through the `NetContext` class.**

## Logging

The application uses Python's built-in logging module to log important events and errors in `logs/` folder or in the console.
* INFO: General information about the application's operation logged in console.
* DEBUG: Detailed debugging information logged in `logs/detailed.log`.
* ERROR: Error messages logged in `logs/errors.log`.

## Authors

* Matteo Baldi - [GitHub]()
* Mattia Cappelletti - [GitHub]()
