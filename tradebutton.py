import eel
from iqoptionapi.stable_api import IQ_Option
from time import sleep
from json import dumps

def tradebutton(config):
    # TRATANDO O OBJETO CONFIG
    config['meta_de_ganhos'] = int(config['meta_de_ganhos'])
    config['stop-loss'] = int(config["stop-loss"])
    
    config['gerenciamento']['mao-fixa'] = int(config['gerenciamento']['mao-fixa'])
    
    if config['gerenciamento']['tipo'] != 'mao-fixa':
        config['gerenciamento']['niveis'] = int(config['gerenciamento']['niveis']) 
    
    if config['copiar_por']['tipo'] == 'posicao':
        config['copiar_por']['valor'] = int(config['copiar_por']['valor']) 
    
    if config['copiar_por']['tipo'] == 'sequencia':
        config['copiar_por']['valor'][0] = int(config['copiar_por']['valor'][0]) 
        config['copiar_por']['valor'][1] = int(config['copiar_por']['valor'][1]) 
    
    if config['copiar_por']['tipo'] == 'id':
        config['copiar_por']['valor'] = int(config['copiar_por']['valor']) 
   
    print(dumps(config, indent=1))
    print('Iniciando tRadeButton!!')
    while True:
        try:
            API = IQ_Option(config['email'], config['password'])
            check, reason = API.connect()
            break
        except:
            pass

    if config['conta'] == 'real':
        API.change_balance('REAL')

    if config['conta'] == 'pratica':
        API.change_balance('PRACTICE')

    if check:
        print('Conectado com sucesso!!')
    else:
        print(f'Deu ruin!! Erro:{reason}')

    if config['opcao'] == 'binaria':
        opcao = 'live-deal-binary-option-placed'
        _tipo = 'binary'

    if config['opcao'] == 'digital':
        opcao = 'live-deal-digital-option'
        _tipo = 'PT1M'

    def payout(par, tipo, timeframe=1):
        if tipo == 'binary':
            a = API.get_all_profit()[par][tipo]
            print(a)
            return a
        elif tipo == 'digital':
            API.subscribe_strike_list(par, timeframe)
            while True:
                d = API.get_digital_current_profit(par, timeframe)
                if d != False:
                    d = int(d)
                    break
                sleep(1)
            API.unsubscribe_strike_list(par, timeframe)
            return int(d)

    def melhor_payout(ativos, opcao):
        print('Escolhendo ativos com maiores payouts!!')
        old = 0
        for a in ativos:
            print(f'Consultando payout de {a}...')
            if config['opcao'] == 'binaria':
                p = payout(a, 'binary')
                if type(p) != float:
                    pass
                else:
                    if p > old:
                        old = p
                        r = a                   
            if config['opcao'] == 'digital':
                p = payout(a, 'digital')
                if p > old:
                    old = p
                    r = a
        print(f'O ativo com maior payout é {r}!!')
        return r

    # work with one trader
    def copiar_por_posicao(p, API):
        print(f'Consultando a posição {p} do Ranking!!')
        f = p + 10
        ranking = API.get_leader_board('Worldwide', p, f, 1)
        for n in ranking['result']['positional']:
            id = ranking['result']['positional'][n]['user_id']
            perfil_info = API.get_user_profile_client(id)
            if perfil_info['status'] == 'online':
                nome = perfil_info['user_name']
                print(f'{nome} está online, copiando id {id}...!!')
                return id

    def copiar_por_id(id, API):
        perfil_info = API.get_user_profile_client(id)
        if perfil_info['status'] == 'online':
            print(f'O trader de ID {id} está online!!')
        else:
            print(f'O trader está offline ou não existe... Copiando dos top 10!!')
            id = copiar_por_posicao(1, API)
        return id

    def copiar_por_nome(nome, API):
        i, f = 1, 100
        print('Procurando trader por nome!!')
        sleep(0.5)
        print('O filtro de nome pode demorar... Anote os IDs ou posições do seus traders favoritos :)')
        while True:
            if f > 10000:
                print(
                    'Nome do trader não encontrado.. O trader está offline ou não existe!! Copiando dos top 10!!')
                id = copiar_por_posicao(1, API)
                break
            ranking = API.get_leader_board('Worldwide', i, f, 0)
            for n in ranking['result']['positional']:
                id = ranking['result']['positional'][n]['user_id']
                perfil_info = API.get_user_profile_client(id)
                if perfil_info['user_name'] == nome:
                    f = 'achou'
                    break
            if f == 'achou':
                break
            i, f = i+100, f+100

        print(f'O ID do {nome} é {id}')
        return id

    def copiar_por_sequencia(config, API):
        ids = []
        print('Baixando Leader Board...', 'green')
        ranking = API.get_leader_board('Worldwide', config['copiar_por']['valor'][0], config['copiar_por']['valor'][1], 0)
        for n in ranking['result']['positional']:
            id = ranking['result']['positional'][n]['user_id']
            perfil_info = API.get_user_profile_client(id)
            if perfil_info['status'] == 'online':
                print(f'Trader de ID {id} está online!!')
                ids.append(id)
        print('Leader Board copiado com sucesso... Estamos quase lá!!')
        return ids

    # work with one trader
    if config['copiar_por']['tipo'] == 'posicao':
        id = copiar_por_posicao(config['copiar_por']['valor'], API)
        id = [id]

    if config['copiar_por']['tipo'] == 'id':
        id = copiar_por_id(config['copiar_por']['valor'], API)
        id = [id]

    if config['copiar_por']['tipo'] == 'nome':
        id = copiar_por_nome(config['copiar_por']['valor'], API)
        id = [id]

    if config['copiar_por']['tipo'] == 'sequencia':
        ativo = melhor_payout(config['ativos'], opcao)
        id = copiar_por_sequencia(config, API)
    else:
        try:
            trader = API.get_users_availability(id)
            if trader['statuses'][0]['selected_instrument_type'] == 'binary-option':
                opcao = 'live-deal-binary-option-placed'
                _tipo = 'binary'

            if trader['statuses'][0]['selected_instrument_type'] == 'digital-option':
                opcao = 'live-deal-digital-option'
                _tipo = 'PT1M'
            ativo = API.get_name_by_activeId(
                trader['statuses'][0]['selected_asset_id']).replace('/', '')
        except:
            ativo = melhor_payout(config['ativos'], opcao)
            seq = {'copiar_por': {'valor': [1, 100]}}
            print('Configurando plano B caso suas configuração fiquem ociosas!!','red')
            id = copiar_por_sequencia(seq, API)

    old = 0
    API.subscribe_live_deal(opcao, ativo, _tipo, 10)
    entrada = config['gerenciamento']['mao-fixa']
    meta = 0
    while True:
        lucro = 0
        trades = (API.get_live_deal(opcao, ativo, _tipo))
        print('Esperando entrada para copiar!!')
        if True:
            if (len(trades) > 0) and (old != trades[0]['user_id']):

                if config['opcao'] == 'digital':
                    status, op = API.buy_digital_spot(
                        ativo, entrada, str(trades[0]["instrument_dir"]).lower(), 1)
                    print(f'Realizando entrada {trades[0]["instrument_dir"]} de ${entrada} na digital!!')
                    while True:
                        if status:
                            status, lucro = API.check_win_digital_v2(op)
                            if status:
                                if lucro > 0:
                                    a = str(round(lucro, 2))
                                    print(f'RESULTADO: | LUCRO: {a}','green')
                                    meta += lucro
                                    
                                    if config['gerenciamento']['tipo'] == 'soros' or config['gerenciamento']['tipo'] == 'soros-gale':
                                        entrada += lucro
                                    break

                                else:
                                    a = str(round(lucro, 2))
                                    print(f'RESULTADO: | LOSS: - {a}','red')
                                    meta -= lucro
                                    
                                    if config['gerenciamento']['tipo'] == 'martin-gale' or config['gerenciamento']['tipo'] == 'soros-gale':
                                        c, e = 1, entrada*2
                                        while True:
                                            if meta >= config['meta_de_ganhos']:
                                                print('Meta de ganhos atingida... Parando!!', 'green')
                                                break
                                            if meta <= -(config['stop_loss']):
                                                stop = config['stop_loss']
                                                print(f'Stop Loss atingido... Parando!!{stop}', 'red')
                                                break
                                            
                                            if config['gerenciamento']['tipo'] == 'martin-gale':
                                                print(
                                                    f'Martingale nivel {c}!!')
                                            if config['gerenciamento']['tipo'] == 'soros-gale':
                                                print(f'Sorosgale nivel {c}!!')
                                            
                                            status, op = API.buy_digital_spot(
                                                ativo, e, str(trades[0]["instrument_dir"]).lower(), 1)
                                            
                                            while True:
                                                status, lucro = API.check_win_digital_v2(
                                                    op)
                                                if status:
                                                    if lucro > 0:
                                                        a = str(round(lucro, 2))
                                                        print(f'RESULTADO: | LUCRO: - {a}','green')
                                                        meta += lucro                                  
                                                        c = config['gerenciamento']['niveis']
                                                        break
                                                    else:
                                                        a = str(round(lucro, 2))
                                                        print(f'RESULTADO: | LUCRO: - {a}','green')
                                                        meta += lucro
                                                        c += 1
                                                        e += e*2.1
                                                        break
                                            if c >= config['gerenciamento']['niveis']:
                                                break
                                    break
                            else:
                                status = True
                        else:
                            break

                if config['opcao'] == 'binaria':
                    status, op = API.buy(entrada, ativo, str(
                        trades[0]["direction"]).lower(), 1)
                    print(f'Realizando entrada {trades[0]["direction"]} de ${entrada} na binária!!', 'green')
                    if status:
                        resposta, lucro = API.check_win_v3(op)
                        if resposta == 'win':
                            a = str(round(lucro, 2))
                            print(f'RESULTADO: | LUCRO: {a}','green')
                            meta += lucro
                            if config['gerenciamento']['tipo'] == 'soros' or config['gerenciamento']['tipo'] == 'soros-gale':
                                entrada += lucro

                        if resposta == 'loose':
                            a = str(round(lucro, 2))
                            print(f'RESULTADO: | LOSS: - {a}','red')
                            meta -= lucro

                            if config['gerenciamento']['tipo'] == 'martin-gale' or config['gerenciamento']['tipo'] == 'soros-gale':
                                c, e = 1, entrada*2
                                while True:
                                    if meta >= config['meta_de_ganhos']:
                                        print('Meta de ganhos atingida... Parando!!','green')
                                        break
                                    if meta <= -(config['stop_loss']):
                                        stop = config['stop_loss']
                                        print(f'Stop Loss atingido... Parando!!{stop}','red')
                                        break
                                    
                                    
                                    if config['gerenciamento']['tipo'] == 'soros-gale' or config['gerenciamento']['tipo'] == 'martin-gale':
                                        if config['gerenciamento']['tipo'] == 'martin-gale':
                                            print(f'Martingale nivel {c}!!')  
                                        if config['gerenciamento']['tipo'] == 'soros-gale':
                                            print(f'Sorosgale nivel {c}!!')
                                        op, op = API.buy(e, ativo, str(
                                            trades[0]["direction"]).lower(), 1)
                                        resposta, lucro = API.check_win_v3(op)
                                        if resposta == 'win':
                                            a = str(round(lucro, 2))
                                            print(f'RESULTADO: | LUCRO: {a}','green')
                                            meta += lucro
                                            c = config['gerenciamento']['niveis']
                                            break
                                        else:
                                            a = str(round(lucro, 2))
                                            print(f'RESULTADO: | LOSS: - {a}','red')
                                            meta += lucro
                                            c += 1
                                            e += e*2.1

                                    if c >= config['gerenciamento']['niveis']:
                                        break
                            else:
                                status = True
                
                if meta >= config['meta_de_ganhos']:
                    print('Meta de ganhos atingida... Parando!!','green')
                    break
                if meta <= -(config['stop_loss']):
                    stop = config['stop_loss']
                    print(f'Stop Loss atingido... Parando!!{stop}','red')
                    break
                old = trades[0]['user_id']
        else:
            pass
        sleep(1)
    API.unscribe_live_deal(opcao, ativo, _tipo)
