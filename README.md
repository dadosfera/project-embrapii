# Text-to-SQL-References
This repository is designed to maintain a curated list of references related Text-to-SQL including State-Of-The-Art, other repositories, code samples and innovative techniques

## Repository Structure
- `dados_datasus/`: DataSUS ingestion, schema, and JDBC-based access (see its README for DB tunnel/test steps).
- `analises/`: Exploratory data analysis notebooks.
- `assets/`: Images and supporting assets.
- `paraphrase-benchmark/`: Benchmark configs for paraphrase evaluation.
- `README.ipynb`: Notebook version of the README/content.
- `ParaphraseEvaluator.py`, `generated_queries.py`, `sample.py`: Supporting scripts.


## Views
- **Nascimento, E.R., García, G., Izquierdo, Y.T. et al.**  
  *LLM-Based Text-to-SQL for Real-World Databases.*  
  SN Computer Science, 6, 130 (2025).  
  [Paper](https://doi.org/10.1007/s42979-025-03662-6) | [Summary](https://drive.google.com/file/d/1W40hXr7tX4bFUlXdvXVg0o9vCHDcA5T4/view?usp=share_link)

- **Nascimento, E., García, G., Feijó, L., Victorio, W., Izquierdo, Y., R. de Oliveira, A., Coelho, G., Lemos, M., Garcia, R., Leme, L., and Casanova, M.**  
  *Text-to-SQL Meets the Real-World.*  
  In *Proceedings of the 26th International Conference on Enterprise Information Systems* (2024).  
  [Paper](https://www.scitepress.org/Papers/2024/125552/125552.pdf) | [Summary](https://drive.google.com/file/d/1GuABoeBN5BNabai9YcjOnWFkpU8gKLcE/view?usp=share_link)

- **Zeshun You, Jiebin Yao, Dong Cheng, Zhiwei Wen, Zhiliang Lu, and Xianyi Shen.**  
  *V-SQL: A View-Based Two-Stage Text-to-SQL Framework.*  
  (2024).  
  [Paper](https://arxiv.org/abs/2502.15686) | [Summary](https://docs.google.com/document/d/1RlnaKtCyDJaInRwjyOQy7yl6qb3hrGSwhHqEC6lfPoE/edit?usp=share_link)


## Surveys
- **Yuyu Luo, Guoliang Li, Ju Fan, Chengliang Chai, and Nan Tang.**  
  *Natural Language to SQL: State of the Art and Open Problems.*  
  PVLDB, 18(12): 5466–5471, 2025.  
  [Paper](https://www.vldb.org/pvldb/vol18/p5466-luo.pdf) | [Summary](https://docs.google.com/document/d/1GTts0oV4Oit7F5WN1X4MbY6XqUXwqy39ZgJrKNxNAyQ/edit?usp=share_link)

- **Ali Mohammadjafari, Anthony S. Maida, and Raju Gottumukkala.**  
  *From Natural Language to SQL: Review of LLM-based Text-to-SQL Systems.*  
  (2025).  
  [Paper](https://arxiv.org/abs/2410.01066) | [Summary](https://drive.google.com/file/d/1B6SWzsw323-TawP7JnKTGz-gK_d-s8Fj/view?usp=share_link)


## Data Lakes

- **Chen, Albert, et al.**  
  *Text-to-SQL for Enterprise Data Analytics.*  
  arXiv preprint arXiv:2507.14372 (2025).  
  [Paper](https://arxiv.org/abs/2507.14372) | [Summary](https://docs.google.com/document/d/1trMHkFNcPq7difFEDmwJ52rj18k5yEUGDwPI2Zv1k5c/edit?usp=share_link)


## AutoViz

- **Dibia, V.**  
  *LIDA: A Tool for Automatic Generation of Grammar-Agnostic Visualizations and Infographics Using Large Language Models.*  
  arXiv preprint arXiv:2303.02927 (2023).  
  [Paper](https://arxiv.org/abs/2303.02927) | [Summary](https://docs.google.com/document/d/12D5qomv_DLx-Y6AkDVXFtOVBOEGa6FYI7LsHx0nMRQE/edit?usp=share_link)

- **Zhang, R., & Elhamod, M.**  
  *Data-to-Dashboard: Multi-Agent LLM Framework for Insightful Visualization in Enterprise Analytics.*  
  arXiv preprint arXiv:2505.23695 (2025).  
  [Paper](https://doi.org/10.48550/arXiv.2505.23695) | [Summary](https://docs.google.com/document/d/1WfBfKqeYcErsC5ZKGZRk8OR09mH2jWGRNju0623sQME/edit?usp=share_link)


## Others
- **Coelho, G.M.C. et al.**  
  *Improving the Accuracy of Text-to-SQL Tools Based on Large Language Models for Real-World Relational Databases.*  
  In: Strauss, C., Amagasa, T., Manco, G., Kotsis, G., Tjoa, A.M., Khalil, I. (eds) Database and Expert Systems Applications. (2024).  
  [Paper](https://link.springer.com/chapter/10.1007/978-3-031-68309-1_8) | [Summary](https://docs.google.com/document/d/16m5Q3qcTOv-D2T0Vdj3XKRsViG-Pi_Yjt1sb2EN-W9M/edit?usp=share_link)

- **Catalina Dragusin∗, Katsiaryna Mirylenka∗, Christoph Miksovic Czasch, Michael Glass, Nahuel Defosse, Paolo Scotton, and Thomas Gschwind.**  
  *Grounding LLMs for Database Exploration: Intent Scoping and Paraphrasing for Robust NL2SQL.*  
  VLDB 2025 Workshop.  
  [Paper](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/AIDB/AIDB25_5.pdf) | [Summary](https://drive.google.com/file/d/1GuABoeBN5BNabai9YcjOnWFkpU8gKLcE/view?usp=share_link)

- **Haoyang Li, Jing Zhang, Hanbing Liu, Ju Fan, Xiaokang Zhang, Jun Zhu, Renjie Wei, Hongyan Pan, Cuiping Li, and Hong Chen.**  
  *CodeS: Towards Building Open-source Language Models for Text-to-SQL.*  
  (2024).  
  [Paper](https://dl.acm.org/doi/10.1145/3654930) | [Summary](https://drive.google.com/file/d/10OO9rddNmqBYfQ9nC_B1rKkI2uM97ujp/view?usp=share_link)

- **Cao, Zhenbiao, et al.**  
  *Rsl-sql: Robust schema linking in text-to-sql generation.*  
  arXiv preprint arXiv:2411.00073 (2024).  
  [Paper](https://arxiv.org/pdf/2411.00073) | [Summary](https://drive.google.com/file/d/1JOwBRarqLgkMctJaNiMHq7if5w-YuoV2/view?usp=share_link)

- **Uber.**  
  *QueryGPT – Natural Language to SQL Using Generative AI.*  
  (2024).  
  [Post](https://www.uber.com/en-BR/blog/query-gpt/) | [Summary](https://docs.google.com/document/d/10kmSiUtzXQND6Aly4SX-W_XrH3kQZPu_wCWXNrfO8RU/edit?usp=share_link)

- **Biswal, Asim, et al.**  
  *Text2SQL is Not Enough: Unifying AI and Databases with TAG.*  
  arXiv preprint arXiv:2408.14717 (2024).  
  [Paper](https://vldb.org/cidrdb/papers/2025/p11-biswal.pdf) | [Summary](https://docs.google.com/document/d/11hFS96xVD9ST5s8e5q-Q5yQaIYI6fmrPmlus91crO3I/edit?usp=share_link)
