
# Relatório de Trade-offs — C3.A2

**Disciplina:** Sistemas Distribuídos e Computação em Nuvem

**Instituição:** FAESA

**Professor:** Howard Cruz Roatti

## 1. Introdução

Este relatório apresenta as principais decisões de arquitetura
adotadas no desenvolvimento da Plataforma de IA como Serviço,
considerando os aspectos de consistência, disponibilidade,
custo, latência e resiliência.

## 2. Teorema CAP

O teorema CAP estabelece que, diante de uma partição de rede,
um sistema distribuído precisa escolher entre garantir
consistência ou disponibilidade.

Na arquitetura desenvolvida, o índice de documentos é
centralizado no serviço de ingestão e persistido em um
arquivo JSON. O Redis também utiliza uma única instância.

Quando o serviço de ingestão fica indisponível, o sistema
não utiliza uma réplica potencialmente desatualizada do
índice. A falha pode ser propagada ao cliente por meio
do código HTTP 503.

Essa decisão favorece a utilização de informações atualizadas,
em detrimento da disponibilidade durante determinadas falhas.
Entretanto, como não existe replicação do índice, o sistema
não oferece garantias formais de consistência distribuída.

Uma alternativa seria implementar réplicas do índice,
aumentando a disponibilidade, mas introduzindo desafios
de sincronização e consistência.

A indexação assíncrona apresenta características de
consistência eventual, pois o Gateway retorna HTTP 202
antes que o documento esteja disponível para consulta.

As retentativas de processamento também podem ocasionar
a indexação duplicada de documentos. Uma melhoria futura
seria implementar mecanismos de idempotência.

## 3. Custo

A utilização do Docker e do Railway facilita a publicação
dos microsserviços e reduz a necessidade de manutenção
manual da infraestrutura.

O projeto foi planejado para utilizar recursos de baixo
custo, considerando os limites dos planos de hospedagem.

A separação da aplicação em microsserviços permite
independência entre os componentes, mas aumenta o consumo
de recursos computacionais.

Cada serviço demanda processamento, memória e
comunicação de rede.

O sistema utiliza um modo simulado de geração de respostas
quando não existe uma chave de API de LLM configurada,
evitando custos com chamadas externas de inteligência
artificial.

O Jaeger é executado localmente, reduzindo a necessidade
de recursos adicionais de observabilidade na nuvem.

## 4. Latência

Uma consulta realizada pelo cliente percorre diferentes
componentes da arquitetura:

Cliente -> Gateway -> Geracao -> Recuperacao -> Ingestao

Essa decomposição facilita a manutenção e a organização
dos serviços, mas acrescenta etapas de comunicação pela rede.

O serviço de recuperação consulta o índice e utiliza
TF-IDF para calcular a similaridade entre a pergunta e
os documentos. O tempo de processamento tende a aumentar
conforme cresce a quantidade de documentos indexados.

A indexação assíncrona reduz o tempo de espera do cliente,
pois o processamento é delegado ao worker por meio do Redis.

No teste local de indexação assíncrona, o Jaeger registrou:

- Duração total de 18,6 milissegundos.
- 16 spans.
- 3 serviços envolvidos no rastreamento.

Esses valores representam uma execução específica no
ambiente local e não constituem uma média de desempenho.

## 5. Resiliência

A plataforma utiliza mecanismos de timeout, retentativas
com espera progressiva e circuit breaker.

As retentativas permitem recuperar determinadas falhas
transitórias, mas aumentam o tempo de resposta quando um
serviço permanece indisponível.

O circuit breaker reduz esse impacto ao interromper
temporariamente novas chamadas ao serviço com falha.

No teste local realizado com o serviço de geração
desligado, foram observados os seguintes resultados:

| Situacao | Tempo aproximado | HTTP |
|---|---|---|
| Antes da abertura do circuito | 18,99 s | 503 |
| Apos a abertura do circuito | 0,0053 s | 503 |

Após a reativação do serviço de geração, a plataforma
voltou a responder normalmente.

Esses resultados demonstram a capacidade do circuit
breaker de evitar chamadas desnecessárias durante
a indisponibilidade de um serviço.

## 6. Limitações e melhorias futuras

- Replicação do índice de documentos.
- Alta disponibilidade do Redis.
- Idempotência na indexação de documentos.
- Escalonamento automático de workers.
- Monitoramento contínuo de métricas.
- Otimização da recuperação de documentos.
- Controle de retentativas em operações de escrita.
- Aprimoramento da segurança do ambiente publicado.

A validação completa na nuvem permanece pendente
devido à indisponibilidade do serviço de recuperação
identificada durante os testes no Railway.

## 7. Considerações finais

As decisões adotadas buscam equilibrar simplicidade,
custo, desempenho e resiliência, considerando o
contexto acadêmico do projeto.

A arquitetura demonstra a aplicação prática dos
conceitos estudados na disciplina, reconhecendo
as limitações e os compromissos envolvidos na
construção de sistemas distribuídos.
