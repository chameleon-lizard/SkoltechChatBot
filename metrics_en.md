# Evaluations

## llama-3.1-8b-instruct vsegpt api, bge-base-en-1.5 embedder, max_iterations=4:

Judge: openai/gpt-4o-2024-08-06

score
5    11
4    22
3    15
2     4
1     6
0    28
Name: count, dtype: int64

Mean score: 3.4827586206896552
Median score: 4.0
Percentage: 69.65517241379311


## qwen-2-7b-instruct vsegpt api, bge-base-en-1.5 embedder, max_iterations=4:

Judge: openai/gpt-4o-2024-08-06

score
5    26
4    27
3    13
2     5
1    10
0     4
Name: count, dtype: int64

Mean score: 3.6666666666666665
Median score: 4.0
Percentage: 73.33333333333333

## qwen-2-7b-instruct vsegpt api, bge-base-en-1.5 embedder, max_iterations=6:

Judge: openai/gpt-4o-2024-08-06

score
5    24
4    26
3    12
2     7
1     9
0     7
Name: count, dtype: int64

Mean score: 3.628205128205128
Median score: 4.0
Percentage: 72.56410256410255

## qwen-2-7b-instruct vsegpt api, bge-base-en-1.5 embedder, paragraph_chunker, 6 chunks:

Judge: openai/gpt-4o-2024-08-06

score
5    26
4    29
3    13
2     8
1     5
0     4
Name: count, dtype: int64

Mean score: 3.7777777777777777
Median score: 4.0
Percentage: 75.55555555555556

## qwen-2-7b-instruct-q8 local, bge-base-en-1.5 embedder, paragraph_chunker, 6 chunks:

Judge: openai/gpt-4o-2024-08-06


score
5    23
4    30
3    10
2     8
1     9
0     5
Name: count, dtype: int64

Mean score: 3.625
Median score: 4.0
Percentage: 72.5


## qwen-2-7b-instruct-q8 local, bge-base-en-1.5 embedder, paragraph_chunker, 6 chunks:

Judge: openai/gpt-4o-mini


score
5    23
4    31
3    10
2     5
1    12
0     4
Name: count, dtype: int64

Mean score: 3.5925925925925926
Median score: 4.0
Percentage: 71.85185185185186


## qwen-2-7b-instruct-q8 local, bge-m3-en-ru embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6: 

Judge: openai/gpt-4o-mini

score
5    24
4    24
3    15
2     4
1    14
0     4
Name: count, dtype: int64

Mean score: 3.493827160493827
Median score: 4.0
Percentage: 69.87654320987654

## qwen-2-7b-instruct-q8 local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6: 

score
5    29
4    28
3    11
2     2
1     8
0     7
Name: count, dtype: int64

Mean score: 3.871794871794872
Median score: 4.0
Percentage: 77.43589743589745

## qwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6: 

Judge: openai/gpt-4o-mini

score
5    27
4    32
3     5
2     4
1     9
0     8
Name: count, dtype: int64

Mean score: 3.831168831168831
Median score: 4.0
Percentage: 76.62337662337661


## meta-llama/llama-3.1-70b-instruct api, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6: 

Judge: openai/gpt-4o-mini

score
5    32
4    23
3     3
2     1
1     2
0    24
Name: count, dtype: int64

Mean score: 4.344262295081967
Median score: 5.0
Percentage: 86.88524590163935


## qwen-2-7b-instruct localqwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt:

Judge: openai/gpt-4o-mini

score
5    27
4    33
3     6
2     3
1    10
0     6
Name: count, dtype: int64

Mean score: 3.810126582278481
Median score: 4.0
Percentage: 76.20253164556962


## qwen-2-7b-instruct localqwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt, manual fixing of thought:
Judge: openai/gpt-4o-mini

score
5    26
4    32
3    11
2     1
1     6
0     9
Name: count, dtype: int64

Mean score: 3.9342105263157894
Median score: 4.0
Percentage: 78.6842105263158

___________________________________________________________________________FIXED QUESTION DATASET________________________________________


## qwen-2-7b-instruct localqwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt, manual fixing of thought:

Eval file: questions_en.json
Model: Qwen/Qwen2-7B-Instruct

Judge: openai/gpt-4o-mini

score
5    19
4    25
3    12
2     1
1     7
0     6
Name: count, dtype: int64

Mean score: 3.75
Median score: 4.0
Percentage: 75.0

## qwen-2-72b-instruct api, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt, manual fixing of thought:

Eval file: questions_en.json
Model: qwen/qwen-2-72b-instruct

Judge: openai/gpt-4o-mini

score
5    10
4    34
3    13
2     2
1     3
0     8
Name: count, dtype: int64

Mean score: 3.7419354838709675
Median score: 4.0
Percentage: 74.83870967741935

