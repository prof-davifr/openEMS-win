# Como o openEMS funciona (em uma página)

## O método FDTD

O openEMS usa o método das **diferenças finitas no domínio do tempo** (FDTD, de
*finite-difference time-domain*):

1. O espaço vira uma **malha** de pequenas caixas retangulares (as células).
2. Em cada célula ficam os campos elétrico **E** e magnético **H** (a célula de Yee).
3. A cada passo de tempo, as equações de Maxwell atualizam **E** a partir de **H**, e **H** a partir de **E**.
4. Uma **excitação** (um pulso gaussiano) entra pela porta da antena. O pulso tem energia em toda a banda de interesse.
5. A simulação para quando a energia na caixa cai abaixo de um limite (`EndCriteria`), por exemplo −40 dB.
6. A **transformada de Fourier** da tensão e da corrente na porta dá S11 e Zin em todas as frequências de uma vez.

## Por que a malha importa

- A célula tem de ser bem menor que o comprimento de onda **no material**: λ = c / (f √εr).
  Uma regra prática é de 15 a 20 células por comprimento de onda na maior frequência.
- Nas bordas de metal, o campo muda muito rápido. A **regra 1/3–2/3** põe uma linha da malha
  1/3 de célula para dentro do metal e outra 2/3 para fora. Isso corrige o tamanho elétrico do patch.
- O passo de tempo depende da **menor** célula (condição de Courant). Uma célula muito pequena
  em qualquer lugar deixa toda a simulação mais lenta.

## Contornos

A caixa de simulação é finita. Nas faces dela, usamos:

- **MUR** ou **PML**: absorvem a onda que sai, como se o espaço continuasse (antena no ar).
- **PEC** (condutor elétrico perfeito): reflete tudo. No `emslab`, a face de baixo é PEC e
  representa o tubo de aço sob o revestimento.

## Materiais com perda

A tangente de perdas (tan δ) entra no openEMS como uma condutividade:
κ = 2π f ε₀ εr tan δ, calculada no centro da banda.

## O que é S11

S11 é a razão entre a onda que volta e a onda que entra na porta. Em dB:
|S11| = 20 log₁₀(|V_refletida / V_incidente|).
Na ressonância, a antena aceita a energia e o |S11| cai. Abaixo de −10 dB, menos de 10 % da potência volta.

## Para saber mais

- Documentação oficial: <https://docs.openems.de>
- Tutoriais em Python: pasta `openEMS\python\Tutorials` dentro de `%LOCALAPPDATA%\openEMS-lab`
- C. A. Balanis, *Antenna Theory*, cap. 14 (antenas patch)
- R. Zoughi, *Microwave Non-Destructive Testing and Evaluation* (2000)
