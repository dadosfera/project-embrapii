## Pré requisitos
- Docker ≥ 20.x


- Docker Compose plugin ≥ 2.x

- Git



Verificar instalação

```bash
docker --version
docker compose version
```


## Construir Docker


Build da imagem Docker

A imagem contém:

Python 3.11

Java (necessário para PySpark)

Todas as dependências do pyproject.toml

Para construir a imagem:
```bash
docker build -t datasus-app .
```

 Rodando o container
 Abrir um shell interativo 
```bash
docker run -it --rm datasus-app bash
```

---

## Como acessar os dados e realizar consultas

A forma de realizar consultas varia de acordo com **o local de execução do código Java**.


### Realizando consultas de dados **fora do servidor do laboratório**

Devido a restrições de acesso da rede da Universidade, para acessar os dados presentes no servidor do laboratório é necessário criar um **tunelamento via SSH**.

Abra um terminal e execute o comando abaixo:

```bash
ssh -L 5433:150.164.2.13:5432 lbduser@150.164.2.44
```

Digite a senha (solicitar ao responsável pelo ambiente).
Esse comando cria o túnel SSH. Em alguns casos, a conexão via túnel tende a ficar suspensa e dar erro por timeout. Basta matar o terminal do túnel e executar o comando novamente. 

Mantenha este terminal aberto durante o uso do banco. 

Em seguida, abra **outro terminal** e certifique-se de ter localmente:

- um arquivo Java de consulta (Ex: `teste2Jdbc.java`)
- o driver JDBC do PostgreSQL (`postgresql-42.7.2.jar`)

Como baixar o driver JDBC do Postgres (se ainda não tiver):
```bash
wget https://jdbc.postgresql.org/download/postgresql-42.7.2.jar
```

Compile e execute:

```bash
javac -cp postgresql-42.7.2.jar teste2Jdbc.java
java -cp .:postgresql-42.7.2.jar teste2Jdbc
```
---

#### Realizando consultas de dados localmente:

Para realizar consultas localmente, basta entrar no diretório `/dados_datasus/jdbc-client` no terminal e rodar os seguintes comandos:


Compilar e executar:
```java
javac -cp postgresql-42.7.2.jar TestJdbc.java
java  -cp .:postgresql-42.7.2.jar TestJdbc
```
