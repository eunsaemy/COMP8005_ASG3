# COMP8005_ASG3

## COMP 8005 - Assignment 3

Design and implement two separate applications:
1. A client application using an architecture that utilizes any API library of your choice.
2. An epoll (edge-triggered) asynchronous server.

### To run server.py:

```python server.py```

### To run client.py:

```python client.py```

### Constraints:

- The server will maintain a list of all connected clients (host names) and store the list together with the number of requests generated by each client and the amount of data transferred to each client.
- Each client will also maintain a record of how many requests it made to the server, the amount of data sent back to server, and the amount of time it took for the server to respond (ie. echo the data back).
- You are required to summarize all your data and findings in a properly formatted technical report. Make extensive use of tables and graphs to support your findings and conclusions.
