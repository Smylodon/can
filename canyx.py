'''
binário
busca por novos e sumidos [OK]
registro de nome do módulo
atualização

'''
import serial.tools.list_ports
import os, sys
from colorama import init, Fore, Back #Importa colorama
import time
from datetime import datetime
from tabulate import tabulate
import requests
import socket

init(autoreset=True)
green = Fore.GREEN
yellow = Fore.YELLOW
red = Fore.RED
white = Fore.WHITE
blue = Fore.BLUE
magenta = Fore.MAGENTA
ciano = Fore.CYAN
greenf = Back.GREEN
yellowf = Back.YELLOW
redf = Back.RED
######## VARIÁVEIS INICIAIS ####
baudrate = 115200
executando = True
consultaID = 0 # irá auxiliar na busca de novos IDs
VERSAO_LOCAL = 0.00002
URL_VERSAO = "https://raw.githubusercontent.com/Smylodon/can/main/versao.txt"
URL_SCRIPT = "https://raw.githubusercontent.com/Smylodon/can/main/canyx.py"  # URL do script no GitHub
NOME_ARQUIVO_LOCAL = "canyx.py"  # Nome do arquivo local que será substituído
############

##### LIMPEZA DE TELA #####
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

# Exemplo de uso
limpar_tela()
###########################

##### ENCONTRANDO PORTA ARDUINO #####
def encontrar_arduino():
    portas = serial.tools.list_ports.comports()
    
    for porta in portas:
        descricao = porta.description.lower()
        if "arduino" in descricao or "usb" in descricao:  # Alguns Arduinos aparecem como "USB Serial Device"
            return porta.device  # Retorna algo como 'COM3' no Windows ou '/dev/ttyUSB0' no Linux
    
    return None  # Nenhum Arduino encontrado

porta_serial = encontrar_arduino()

if porta_serial:
    print(f"{ciano}>>> {white}Dispositivo CAN encontrado na porta: {yellow}{porta_serial}")
else:
    print(red + '*-' * 30)
    print(red + '>>> ' + white + 'Nenhuma porta com Dispositivo CAN foi encontrada.')
    print(red + '>>> ' + white + 'Confira se o Dispositivo CAN está conectado ao computador corretamente ou experimente outra porta.')
    print(red + '*-' * 30)
    sys.exit()
###########################

print (yellow + '>>>' + white + ' AGUARDE...')
ser = serial.Serial(porta_serial, baudrate, timeout=1)
time.sleep(2)  # Aguarda estabilização da comunicação


def apenasver():
    with open("personalizado.txt", "w", encoding="utf-8") as arquivo:
        print(f"Para {red}SAIR {white} digite {red}CTRL+C{white} em qualquer momento")
        print(f"{yellow}>>> {white}Aguardando mensagens do Dispositivo CAN... (Capturando TODOS os dados)")
        print(magenta+"Caso demore mais que 6 segundos para surgir dados veja as conecções CAN_L e CAN_H")
        for i in range(1, 6):
            print("." * i)  # Imprime os pontos de forma incremental
            time.sleep(1)  # Aguarda 1 segundo
        while executando:
            # Verifica se há dados disponíveis na porta serial
            if ser.in_waiting > 0:
                dados = ser.readline()  # Lê uma linha da serial
                
                try:
                    mensagem = dados.decode('ISO-8859-1', errors="ignore").strip().upper()  # Decodifica e trata erros
                except UnicodeDecodeError:
                    print("Erro na decodificação, ignorando linha...")
                    continue  # Pula para a próxima leitura
                
                # Captura horário exato com milissegundos
                timestamp = datetime.now().strftime("%H:%M:%S.%f ")[:-3]  # Formato: [HH:MM:SS.sss]

                # Grava todos os dados, sem filtro de ID
                mensagem_formatada = f"{ciano}{timestamp}{white} {mensagem}"
                print(mensagem_formatada)  # Exibe no terminal
                arquivo.write(mensagem_formatada + "\n")  # Grava no arquivo
                arquivo.flush()  # Garante que os dados sejam salvos imediatamente


def buscaID():
    global consultaID
    if consultaID == 0:# Usamos um set para garantir que os IDs sejam únicos
        ids_unicos = set()
        dados_para_tabela = []  # Lista para armazenar os dados para a tabela

        # Arquivo para gravar os IDs
        with open("ids.txt", "w", encoding="utf-8") as arquivo:
            print(yellow + '>>>' + white + " Aguarde a captura dos IDs... (+/- 6 seg.)")

            # Tempo de 5 segundos para captura de dados
            tempo_limite = time.time() + 5
            ids_capturados = False  # Flag para verificar se algum ID foi capturado

            while time.time() < tempo_limite:
                # Verifica se há dados disponíveis
                if ser.in_waiting > 0:
                    dados = ser.readline()  # Lê uma linha da serial
                    
                    try:
                        mensagem = dados.decode('ISO-8859-1', errors="ignore").strip().upper()  # Decodifica e trata erros
                    except UnicodeDecodeError:
                        continue  # Pula para a próxima leitura em caso de erro

                    # Verifica se a mensagem contém um ID no formato '0X...' 
                    if "ID:" in mensagem:
                        # Extrai o ID, assumindo que o formato seja sempre 'ID: 0X...'
                        id_inicio = mensagem.find("ID:") + 4  # 4 para pular 'ID: '
                        id_fim = mensagem.find(" ", id_inicio)  # Encontra o próximo espaço após o ID
                        id_extraido = mensagem[id_inicio:id_fim]  # Extrai o ID

                        # Se o ID não for repetido, adiciona ao conjunto de IDs únicos
                        if id_extraido not in ids_unicos:
                            ids_unicos.add(id_extraido)  # Adiciona o ID ao conjunto de IDs únicos
                            #print(f"{ciano}ID: {id_extraido}") # PRINTA IDs EM TELA
                            arquivo.write(id_extraido + "\n")
                            arquivo.flush()  # Garante que os dados sejam salvos imediatamente
                            # Adiciona o ID à lista para exibição na tabela com índice
                            dados_para_tabela.append([len(dados_para_tabela) + 1, id_extraido])

                        ids_capturados = True

            # Verifica se algum ID foi capturado
            if not ids_capturados:
                print(red + '>>>' + white + " Nenhum dado foi recebido do Arduino durante o período de 5 segundos.")
            else:
                print(f'{yellow}\n>>> {white}IDs capturados e gravados no arquivo {red}ids.txt {white}com sucesso.')

                # Exibe os dados capturados na tabela
                if dados_para_tabela:
                    headers = ["N.", "IDs identificados"]  # Cabeçalho da tabela
                    print(tabulate(dados_para_tabela, headers=headers, tablefmt="pipe"))
            
            consultaID = 1
            escbuscaID()
    else:
        print(f'{green}\nRealizando nova busca para comparação...\n')
        
        # Carregar IDs da primeira busca
        with open("ids.txt", "r", encoding="utf-8") as arquivo:
            ids_anteriores = set(arquivo.read().splitlines())
        
        # Nova captura de IDs
        ids_novos = set()
        tempo_limite = time.time() + 5
        while time.time() < tempo_limite:
            if ser.in_waiting > 0:
                dados = ser.readline()
                try:
                    mensagem = dados.decode('ISO-8859-1', errors="ignore").strip().upper()
                except UnicodeDecodeError:
                    continue
                if "ID:" in mensagem:
                    id_inicio = mensagem.find("ID:") + 4
                    id_fim = mensagem.find(" ", id_inicio)
                    id_extraido = mensagem[id_inicio:id_fim]
                    ids_novos.add(id_extraido)
        
        # Comparação
        ids_apareceram = ids_novos - ids_anteriores
        ids_sumiram = ids_anteriores - ids_novos
        
        # Gravar os novos e desaparecidos
        with open("ids_novos.txt", "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(ids_apareceram))
        
        with open("ids_desaparecidos.txt", "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(ids_sumiram))
        
        # Preparar dados para exibição
        max_linhas = max(len(ids_anteriores), len(ids_apareceram), len(ids_sumiram))
        tabela = []
        ids_anteriores_lista = list(ids_anteriores) + ["-"] * (max_linhas - len(ids_anteriores))
        ids_apareceram_lista = list(ids_apareceram) + ["-"] * (max_linhas - len(ids_apareceram))
        ids_sumiram_lista = list(ids_sumiram) + ["-"] * (max_linhas - len(ids_sumiram))
        
        for i in range(max_linhas):
            tabela.append([i + 1, ids_anteriores_lista[i], ids_apareceram_lista[i], ids_sumiram_lista[i]])
        
        # Exibir tabela
        headers = ["N.", "IDs da primeira busca", "IDs novos", "IDs ausentes"]
        print(tabulate(tabela, headers=headers, tablefmt="pipe"))
        escbuscaID()


def escbuscaID():
    global consultaID
    while True:
        modoopbusca = input(ciano+'\n  >>' + white+' Selecione uma opção para busca de ID: '+
                        blue+'\n  >>'+ white +' 1 - Primeira busca'+
                        magenta+'\n  >>'+ white +' 2 - Segunda busca'+
                        yellow+'\n  >>'+ white +' 3 - Voltar no menu anterior'+ 
                        blue+'\n\n  >>'+ white +' 4 - '+ red +'Sair'+
                        ciano+'\n    --> '+white)
        modoopbusca = int(modoopbusca)
        if modoopbusca == 1:
            if consultaID == 0: 
                buscaID()
            else:
                while True:
                    print(f'{red} >>> {white}Não é a primeira busca feita, deseja refazer a primeira busca?')
                    op = input("    S - sim | N - não" +
                               "\n    --> ").strip().upper()
                    if op == 'S':
                        consultaID = 0
                        buscaID()
                        break
                    if op == 'N':
                        limpar_tela()
                        entrada()
                        break
                    else:
                        print(f'Entrada inválida! Você digitou: {op}. Tente novamente')
            break
        if modoopbusca == 2:
            if consultaID == 0:
                print(f'{red}*** ATENÇÃO! ***')
                print("Não foi feita a primeira busca, é necessário fazê-la para ter parâmetro de comparação.\n")
            else:
                buscaID()
                break            
        if modoopbusca == 3: 
            limpar_tela()
            entrada()
            break
        if modoopbusca == 4:
            ser.close()
            print("\nPorta serial fechada. Programa finalizado.\n")
            break
        else:
            print('Escolha incorreta! Digite uma das opções abaixo:')

def especID():
    id_desejado = input("Digite o ID em HEXADECIMAL que deseja visualizar (ex.: A12): ").strip().replace(".", "0").upper()

    with open("id_especifico.txt", "w", encoding="utf-8") as arquivo:
        print(f"Para {red}SAIR {white} digite {red}CTRL+C{white} em qualquer momento")
        print(f"{yellow}>>> {white}Aguardando mensagens do Dispositivo CAN... (Filtrando ID: {id_desejado})")

        while True:
            time.sleep(5)  # Aguarda 5 segundos antes de verificar os dados
            if ser.in_waiting == 0:
                print(f"{red}>>> {white}Nenhum dado encontrado no barramento. Tentando novamente em 5 segundos...")
                continue  # Volta para o início do loop e espera mais 5 segundos
            
            while executando:
                # Verifica se há dados disponíveis na porta serial
                if ser.in_waiting > 0:
                    dados = ser.readline()  # Lê uma linha da serial
                    
                    try:
                        mensagem = dados.decode('ISO-8859-1', errors="ignore").strip().upper()  # Decodifica e trata erros
                    except UnicodeDecodeError:
                        print("Erro na decodificação, ignorando linha...")
                        continue  # Pula para a próxima leitura
                    
                    # Captura horário exato com milissegundos
                    timestamp = datetime.now().strftime("%H:%M:%S.%f ")[:-3]  # Formato: [HH:MM:SS.sss]

                    # Verifica se a mensagem contém o ID desejado
                    if id_desejado in mensagem:
                        mensagem_formatada = f"{ciano}{timestamp}{white} {mensagem}"
                        print(mensagem_formatada)  # Exibe no terminal
                        arquivo.write(mensagem_formatada + "\n")  # Grava no arquivo
                        arquivo.flush()  # Garante que os dados sejam salvos imediatamente


def entrada() :
    while True:
        modoop = input(ciano+'\n  >>' + white+' Selecione uma opção: '+
                        blue+'\n  >>'+ white +' 1 - Apenas ver conexão de dados'+
                        magenta+'\n  >>'+ white +' 2 - Buscar IDs no barramento'+
                        yellow+'\n  >>'+ white +' 3 - Analisar ID específico'+
                        blue+'\n\n  >>'+ white +' 4 - '+ red +'Sair'+
                        ciano+'\n    --> '+white)

        modoop = int(modoop)
        
        if modoop == 1: 
            apenasver()
            break
        if modoop == 2:
            limpar_tela() 
            escbuscaID()
            break
        if modoop == 3: 
            especID()
            break
        if modoop == 4:
            ser.close()
            print("\nPorta serial fechada. Programa finalizado.\n")
            break
        else:
            print(' Escolha incorreta! Digite uma das opções abaixo:')

def verificar_conexao_ip():
    """Verifica se o computador tem conexão com a internet, tentando conectar ao IP 1.1.1.1."""
    try:
        socket.create_connection(("1.1.1.1", 80), timeout=5)
        return True
    except (socket.timeout, socket.error):
        return False

def verificar_github():
    """Verifica se o GitHub está online tentando acessar o arquivo versao.txt."""
    try:
        resposta = requests.get(URL_VERSAO)
        if resposta.status_code == 200:
            return resposta.text.strip()  # Retorna o conteúdo do arquivo versao.txt
        else:
            print(f"Erro ao acessar o GitHub. Código de status: {resposta.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Erro ao acessar GitHub: {e}")
        return None

def atualizar_script():
    """Apaga o script atual, baixa a versão mais recente e substitui o arquivo."""
    try:
        # Passo 1: Apagar o arquivo atual
        if os.path.exists(NOME_ARQUIVO_LOCAL):
            os.remove(NOME_ARQUIVO_LOCAL)
            print(f"{green}>>> {white}Arquivo antigo apagado com sucesso!")
        else:
            print(f"{red}>>> {white}Arquivo não encontrado!")

        # Passo 2: Baixar o novo arquivo do GitHub
        resposta = requests.get(URL_SCRIPT)
        if resposta.status_code == 200:
            with open(NOME_ARQUIVO_LOCAL, 'wb') as arquivo_local:
                arquivo_local.write(resposta.content)
            print(f"{green}>>> {white}Novo atualização baixada e salva com sucesso!")

            # Passo 3: Solicitar que o usuário reabra o programa
            print(f"{yellow}>>> {white}Por favor, reabra o programa para usar a versão mais recente.")
            print(f"{yellow}>>> {white}O programa será encerrado automaticamente agora.")
            
            # Passo 4: Encerra o programa após a atualização
            exit()
        else:
            print(f"{red}>>> {white} Erro ao baixar o script. Código de status: {resposta.status_code}")
    except requests.RequestException as e:
        print(f"{red}>>> {white}Erro ao acessar o GitHub: {e}")
    except Exception as e:
        print(f"{red}>>> {white}Erro inesperado: {e}")

def comparar_versionamento(versao_online):
    """Compara a versão online com a versão local e pergunta se quer atualizar."""
    try:
        versao_online_float = float(versao_online)
        print(f'{green}\nExiste uma atualização deste programa.')
        print(f'{green}Versão online: {white}{versao_online_float:.5f}')
        print(f'{green}Versão local: {white}{VERSAO_LOCAL:.5f}\n')
        if versao_online_float > VERSAO_LOCAL:
            while True:
                atualizar = input(f'{yellow}Deseja atualizar para a nova versão? (s/n): ').strip().lower()
                if atualizar == 's':
                    print("Atualizando para a versão mais recente...")
                    # Aqui você pode adicionar o código para atualizar o script
                    break
                elif atualizar == 'n':
                    print("Mantendo a versão atual.")
                    entrada()
                    break
                else:
                    print("Resposta inválida! Por favor, digite 's' para sim ou 'n' para não.")
        else:
            print(f"A versão online ({versao_online_float:.5f}) é menor ou igual à versão local ({VERSAO_LOCAL:.5f}).")
    except ValueError:
        print("Erro ao converter a versão para número.")


if verificar_conexao_ip():
    versao_online = verificar_github()
    if versao_online:
        comparar_versionamento(versao_online)
    else:
        entrada()
else:
    entrada()