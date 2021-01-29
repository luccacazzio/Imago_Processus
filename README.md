# Imago Processus

Software usado para manipulação de imagens de mamografias a fim de classificá-las na escala BIRADS. Essa é uma escala que define a densidade como sendo ou quase inteiramente composta por gordura (densidade I), por tecido fibrobroglandular difuso (densidade II), por tecido denso heterogêneo (III) ou por tecido extremamente denso (IV). Para realizar o treinamento e a classificação, usamos a distância de Mahalanobis das seguintes características: 

- Energia
- Entropia
- Homogeneidade
- Contraste
- Momentos invariantes de Hu

escolhidas pelo usuário.

### Instalando as Dependências

1. pip3 install -r requirements.txt


### Uso

```
python3 imagoProcessus.py
```

**[GNU GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html)**
