# Fase 1: Build dell'ambiente
FROM python:3.13 AS deps

RUN apt-get update && apt-get install -y wget build-essential expect perl dos2unix

# Imposta la directory di lavoro
WORKDIR /install

# Scarica il tarball di SICStus Prolog per Linux
RUN wget -O sicstus.tar.gz "https://sicstus.sics.se/sicstus/products4/sicstus/4.6.0/binaries/linux/sp-4.6.0-x86_64-linux-glibc2.17.tar.gz"

# Estrai l'archivio
RUN tar -xzf sicstus.tar.gz

# Copiamo lo script del nostro "robot"
COPY install_sicstus.exp /install/

RUN dos2unix /install/install_sicstus.exp && chmod +x /install/install_sicstus.exp

# Eseguiamo lo script per installare SICStus
RUN cd sp-4.6.0-x86_64-linux-glibc2.17 && /install/install_sicstus.exp

# Aggiungi l'eseguibile di SICStus al PATH di sistema
ENV PATH="/usr/local/sicstus/bin:${PATH}"

# Pulisci i file di installazione
RUN rm -rf /install

# --- Installa le dipendenze Python ---
WORKDIR /dalia
COPY ./requirements.txt /dalia/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get install -y --no-install-recommends net-tools && apt-get clean && rm -rf /var/lib/apt/lists/*

# Fase 2: Immagine finale
FROM deps
WORKDIR /dalia
COPY ./ /dalia

CMD ["python", "main.py"]