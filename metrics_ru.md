## qwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt, manual fixing of thought:

Eval file: questions_ru.json
Model: Qwen/Qwen2-7B-Instruct

Judge: openai/gpt-4o-mini

score
5    12
4    24
3     9
2     4
1     9
0     9
Name: count, dtype: int64

Mean score: 3.4482758620689653
Median score: 4.0
Percentage: 68.9655172413793


## qwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt, manual fixing of thought, fixed translate:

Eval file: questions_ru.json
Model: Qwen/Qwen2-7B-Instruct

Judge: openai/gpt-4o-mini

score
5    17
4    21
3    10
2     4
1     7
0     8
Name: count, dtype: int64

Mean score: 3.6271186440677967
Median score: 4.0
Percentage: 72.54237288135593


## qwen-2-72b-instruct api, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, with qwen translation prompt, manual fixing of thought:

Eval file: questions_ru.json
Model: qwen/qwen-2-72b-instruct

Judge: openai/gpt-4o-mini

score
5    17
4    29
3     5
2     2
1     3
0    11
Name: count, dtype: int64

Mean score: 3.982142857142857
Median score: 4.0
Percentage: 79.64285714285715


## qwen-2-7b-instruct local, BAAI/bge-large-en-v1.5 embedder, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, hybrid search, bm25 chunk size 100/10, with qwen translation prompt, manual fixing of thought, fixed translate:

Eval file: questions_ru.json
Model: Qwen/Qwen2-7B-Instruct

Judge: openai/gpt-4o-mini

score
5    17
4    26
3    10
2     1
1     7
0     6
Name: count, dtype: int64

Mean score: 3.737704918032787
Median score: 4.0
Percentage: 74.75409836065575

## qwen-2-7b-instruct api, intfloat/multilingual-e5-large-instruct embedder, translate, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, hybrid search, bm25 chunk size 100/10, with qwen translation prompt, manual fixing of thought, fixed translate:
Eval file: questions_ru.json                                        
Model: qwen/qwen-2-7b-instruct                                      

Judge: openai/gpt-4o-mini                                           

score                                                               
5    14                                                             
4    26                                                             
3     9                                                             
2     1                                                             
1     9                                                             
0     8                                                             
Name: count, dtype: int64                                           

Mean score: 3.593220338983051                                       
Median score: 4.0                                                   
Percentage: 71.86440677966101


## qwen-2-7b-instruct api, intfloat/multilingual-e5-large-instruct embedder, no translate, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, hybrid search, bm25 chunk size 100/10, with qwen translation prompt, manual fixing of thought, fixed translate:
Eval file: questions_ru.json                                        
Model: qwen/qwen-2-7b-instruct                                      

Judge: openai/gpt-4o-mini                                           

score                                                               
5    19                                                             
4    21                                                             
3     9                                                             
2     6                                                             
1     7                                                             
0     5                                                             
Name: count, dtype: int64                                           

Mean score: 3.629032258064516                                       
Median score: 4.0                                                   
Percentage: 72.58064516129032


## qwen-2-7b-instruct api, intfloat/multilingual-e5-large-instruct embedder, no translate for embedder, translate for bm25, paragraph_chunker, 24 chunks, BAAI/bge-reranker-v2-m3 reranker, top-n 6, hybrid search, bm25 chunk size 100/10, with qwen translation prompt, manual fixing of thought, fixed translate:
Eval file: questions_ru.json
Model: qwen/qwen-2-7b-instruct

Judge: openai/gpt-4o-mini

score
5    15
4    26
3     8
2     1
1     8
0     9
Name: count, dtype: int64

Mean score: 3.6724137931034484
Median score: 4.0
Percentage: 73.44827586206897

