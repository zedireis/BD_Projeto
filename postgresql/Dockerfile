# 
# Bases de Dados 2020/2021
# Trabalho Prático
#
# Authors: 
#   José Reis - 2018285575
#   Nuno Silva - 2018285621
#   University of Coimbra

FROM library/postgres


ENV POSTGRES_USER aulaspl
ENV POSTGRES_PASSWORD aulaspl
ENV POSTGRES_DB projeto

COPY BD2021_data.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
