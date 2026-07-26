# Vector Search

Finding and retrieving similar items in large data sets by comparing their vector representation. Vector search looks for similarity based on meaning and context. The distance between two vectors can be used to indicate similarity. There are many different distance metrics. The task of a vector database is to identify and retrieve a list of vectors that are closest to the vector of a query, using **distance metrics and a search algorithm**.


## Distance Metrics

- The core problem is to judge the distance between two vectors. This is done using various distance metrics. This is a function that takes two vectors as input and produce a distance value between them.
- The distance can take many shapes, it can be the geometric distance between two points, it could be an angle between the vectors, it could be a count of vector component differences, etc.
- Depending on the machine learning models vectors can go ~100 or go into thousands of dimensions
- The more dimensions there are the more time it takes to compute the distance between two vectors. Some similarity measures are more compute heavy than others. Therefore, different distance metrics balances the speed and accuracy of calculating distance.
- Choose a distance metrics that matches the model you are using. 

### Cosine similarity

- Uses angle between to vectors to measure distance. The smaller the angle the more similar. Mostly used in NLP. It measures similarity between documents regardless of magnitude.
- It reports angle of data

### Dot product

- Multiple two or more vectors
- It reports both angle and magnitude

### Squared Euclidean (L2- Squared)

- Sume of squared vector

### Manhattan (L1 Norm or Taxicab Distance)

- Compares the distance between a pair of vectors
- This is faster compared to L2 which is more accurate

### Hamming

- It computes how many changes are needed to convert one vector into another

## Search Algorithm 

- KNN (K Neariest Neighbour)
- ANN (Approximate Nearest Neighbour)

ANN algo is used by vector databases. In indexes the vectors using ANN algo and stores the nearest vectors close together which enables faster search.

## pgvector

Supports the following distance function

- L2 distance
- (negetive) inner product
- cosine distance
- L1 distance
- Hamming distance (binary vectors)
- Jaccard distance (binary vectors)
