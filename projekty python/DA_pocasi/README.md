# Bee IT

## Kurz jazyka Python

### Projekt 2: Datový dashboard pro předpověd počasí

Cílem projektu je vytvoření programu, který zobrazí datový dashboard pro vizualizac předpovědi počasí a vypíše zajímavé informace o počasí s využitím internetových služeb. Pro využití služeb se budete muset registrovat na jejich webové stránce a získat privátní klíč, který v aplikaci uvedete. Klíče se typicky zapisují do souborů s příponou .env ve tvaru klíč=hodnota. Návod na vytvoření takového souboru s registrací potřebné služby je v sešitě s prvním týdnem výuky. 

Pro ukázku zde máte vytvořený hotový dashboard v souboru app.py. Pro spuštění datového dashboardu budete potřebovat .env soubor s klíčem pro službu openweathermap. Získat klíč můžete po registraci na stránce: https://api.openweathermap.org/. Klíč si uložte do .env souboru ve tvaru: USER_KEY=váš klíč. Dále si vytvořte virtuální prostředí pomocí příkazu v terminálu: ```python3 -m venv venv``` a aktivujte si ho pomocí příkazu: ```venv\Scripts\activate``` na operačních systémech Windows nebo ```source venv/bin/activate``` na operačních systémech MacOS a Linux. Dále si musíte nainstalovat všechny potřebné závislosti ze souboru requirements.txt pomocí příkazu: ```pip install -r requirements.txt```. Na závěr můžete spustit datových dashboard příkazem: ```python app.py```.

Vaším úkolem je vytvořit obdobný program pro předpověd a vizualizaci dat o počasí v datovém dashboardu. K dispozici máte v adresáři ```cviceni``` 4 jupyter sešity, které vás naučí potřebným základním znalostem pro dokončení projektu. Adresář si můžete také stáhnout k sobě do pracovního prostředí. Hotový program v souboru ```app.py``` slouží jen jako cíl, kterého byste měli dosáhnout. Měli byste se vyhnout kopírování kódu z tohoto souboru.

Cvičení v Jupyter notebookách mají následující témata:

<table>
    <thead>
        <tr>
            <th>Číslo tématu</th><th>Název tématu</th><th>Odkaz na sešit</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td><td>Práci se službami</td><td><a href="./cviceni/tyden1/cviceni1.ipynb">Týden 1</a></td>
        </tr>
        <tr>
            <td>2</td><td>Tvorba dashboardu v Dash</td><td><a href="#">Chystá se</a></td>
        </tr>
        <tr>
            <td>3</td><td>Reaktivní programování v Dash</td><td><a href="#">Chystá se</a></td>
        </tr>
        <tr>
            <td>4</td><td>Responzivní webdesign v Dash</td><td><a href="#">Chystá se</a></td>
        </tr>
    </tbody>
</table>

Doporučuji si stáhnotu celou složku se cvičeními, kde máte i potřebné datové zdroje: [ZDE](./cviceni)

