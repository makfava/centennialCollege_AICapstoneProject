# Download de Datasets TTC

Este documento descreve como fazer o download dos datasets TTC usando o browser do Cursor.

## Problema

Os datasets TTC são carregados dinamicamente via JavaScript, então scripts simples de scraping não funcionam. É necessário usar um browser com JavaScript habilitado.

## Solução

Use o browser do Cursor para acessar as páginas e fazer o download dos arquivos manualmente, ou use o script `download_ttc_datasets.py` com Selenium (requer ChromeDriver ou GeckoDriver).

## URLs dos Datasets

1. TTC Streetcar Delay Data: https://open.toronto.ca/dataset/ttc-streetcar-delay-data/
2. TTC Bus Delay Data: https://open.toronto.ca/dataset/ttc-bus-delay-data
3. TTC LRT Delay Data: https://open.toronto.ca/dataset/ttc-lrt-delay-data/
4. TTC Subway Delay Data: https://open.toronto.ca/dataset/ttc-subway-delay-data/

## Como usar o browser do Cursor

1. Navegue para cada URL usando o browser do Cursor
2. Aguarde a página carregar completamente
3. Clique nos links de download (eles aparecem como "Download [dataset-name] dataset in XLSX format")
4. Os arquivos serão baixados para a pasta `dataset/`

## Scripts Disponíveis

- `download_ttc_datasets.py`: Script usando Selenium (requer ChromeDriver)
- `extract_and_download_ttc.py`: Script usando requests (não funciona porque conteúdo é JS)
- `download_ttc_final.py`: Template para adicionar URLs manualmente

## Nota

O script Selenium pode não funcionar se o ChromeDriver não estiver instalado ou configurado corretamente.
