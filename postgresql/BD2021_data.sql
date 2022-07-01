/* 
	# 
	# Bases de Dados 2020/2021
	# Trabalho Prático
	#
*/


/* 
   Fazer copy-paste deste ficheiro
   para o Editor SQL e executar.
*/

/* 
Estes dois comandos drop (comentados) permitem remover as tabelas emp e dep da base de dados (se ja' tiverem sido criadas anteriormente)

drop table emp;
drop table dep;
*/

CREATE TABLE pessoa (
	id	 BIGSERIAL,
	nome	 VARCHAR(100),
	email	 VARCHAR(50) UNIQUE,
	username VARCHAR(20) UNIQUE,
	password VARCHAR(20),
	morada	 VARCHAR(512),
	PRIMARY KEY(id)
);

CREATE TABLE artigo (
	id	 CHAR(10),
	nome VARCHAR(50),
	PRIMARY KEY(id)
);

CREATE TABLE leilao (
	id	 BIGSERIAL,
	preco_min NUMERIC(8,2),
	data_fim	 TIMESTAMP,
	pessoa_id BIGINT NOT NULL,
	artigo_id CHAR(10) NOT NULL,
	last_version_id BIGINT,
	PRIMARY KEY(id)
);

CREATE TABLE mensagem (
	id	 BIGSERIAL,
	texto	 VARCHAR(512),
	data	 TIMESTAMP,
	pessoa_id BIGINT NOT NULL,
	leilao_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE licitacao (
	id	 BIGSERIAL,
	preco	 NUMERIC(8,2),
	leilao_id BIGINT NOT NULL,
	pessoa_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE versao (
	id	 BIGSERIAL,
	titulo	 VARCHAR(50),
	descricao VARCHAR(512),
	leilao_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE notificacao (
	id	 BIGSERIAL,
	texto	 VARCHAR(512),
	data	 TIMESTAMP,
	pessoa_id BIGINT NOT NULL,
	leilao_id BIGINT NOT NULL,
	from_id BIGINT NOT NULL,
	PRIMARY KEY(id)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk2 FOREIGN KEY (artigo_id) REFERENCES artigo(id);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk3 FOREIGN KEY (last_version_id) REFERENCES versao(id);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);
ALTER TABLE versao ADD CONSTRAINT versao_fk1 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk1 FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk2 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk3 FOREIGN KEY (from_id) REFERENCES pessoa(id);

create or replace function notify_msg() returns trigger
language plpgsql
as $$
declare
	c1 cursor for
		select DISTINCT(pessoa_id)
		from mensagem
		where leilao_id = new.leilao_id
		order by pessoa_id;
		
	c2 cursor for
		select pessoa_id
		from leilao
		where id = new.leilao_id;
		
	pessoa mensagem.pessoa_id%type;
	owner mensagem.pessoa_id%type;
begin
	open c2;
	fetch c2 into owner;
	if(new.pessoa_id != owner) then
		insert into notificacao (texto, data, pessoa_id, leilao_id, from_id)
		values(new.texto, new.data, owner, new.leilao_id, new.pessoa_id);
	end if;
	close c2;
	
	open c1;
	loop
		fetch c1 into pessoa;
		exit when not found;
		continue when pessoa = owner;
		continue when pessoa = new.pessoa_id;
		insert into notificacao (texto, data, pessoa_id, leilao_id, from_id)
		values(new.texto, new.data, pessoa, new.leilao_id, new.pessoa_id);
	end loop;
	
	return new;
end;
$$;

create trigger trig2
after insert on mensagem
for each row
execute procedure notify_msg();


create or replace function update_last_version() returns trigger
language plpgsql
as $$
begin
	UPDATE leilao SET last_version_id = new.id WHERE leilao.id = new.leilao_id;
	return new;
end;
$$;

create or replace function insert_new_licitation(leilaoId integer, preco_licitacao numeric, userId integer) returns integer
language plpgsql
as $$
DECLARE

  licitacao_max   NUMERIC(8,2);
  
BEGIN

  PERFORM id
  FROM leilao
  WHERE id = leilaoId AND data_fim > CURRENT_TIMESTAMP(0);

  if not found then
     RETURN 2;
  end if;

  SELECT preco
  FROM licitacao
  INTO licitacao_max
  WHERE leilao_id = leilaoId
  ORDER BY preco DESC
  LIMIT 1
  FOR UPDATE;

  if not found then
      SELECT preco_min
      FROM leilao
      INTO licitacao_max
      WHERE id = leilaoId;

      if preco_licitacao >= licitacao_max then
          INSERT INTO licitacao (preco, leilao_id, pessoa_id)
          VALUES (preco_licitacao, leilaoId, userId);
	  RETURN 1;
      else
	RETURN  0;
      end if;
  else
      if preco_licitacao > licitacao_max then
          INSERT INTO licitacao (preco, leilao_id, pessoa_id)
          VALUES (preco_licitacao, leilaoId, userId);
	  RETURN 1;
      else
	RETURN  0;
      end if;
  end if;

END;
$$;

create trigger trig1
after insert on versao
for each row
execute procedure update_last_version();


INSERT INTO pessoa (nome, email, username, password, morada) VALUES ('Nelso', 'nelso@email.com', 'nelso', '123', 'Rua da Ruela');
INSERT INTO pessoa (nome, email, username, password, morada) VALUES ('Vitor', 'vitor@email.com', 'vitor', '12345', 'Rua da Ruela, nº2');


INSERT INTO artigo (id, nome) VALUES ('1234567890', 'Candeeiro');
INSERT INTO artigo (id, nome) VALUES ('0123456789', 'Sofa');

INSERT INTO leilao (preco_min, data_fim, pessoa_id, artigo_id) VALUES ('20', '2021-06-28 14:56:21', '1', '1234567890');
INSERT INTO versao (titulo, descricao, leilao_id) VALUES ('Venda de candeeiro', 'Lampada incluida', '1');
INSERT INTO versao (titulo, descricao, leilao_id) VALUES ('Venda de candeeiro V2', 'Lampada não incluida', '1');

INSERT INTO leilao (preco_min, data_fim, pessoa_id, artigo_id) VALUES ('50', '2021-06-28 16:56:21', '2', '0123456789');
INSERT INTO versao (titulo, descricao, leilao_id) VALUES ('Venda de sofa-cama', 'Falta colchão', '2');

