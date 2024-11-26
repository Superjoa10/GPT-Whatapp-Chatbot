# Contains all extra, text based only, messages that are used in the app

# Starter messages

first_hotel_message = """Você Selecionou o Hotel em Fortaleza / Bahia, com a localização fantasia ao lado da prefeitura de Fortaleza, na Rua Chile numero 296, Centro.
Esse assistente tem como objetivo ser um atendente de alto nivel e educação, te da informações sobre sua estadia, regras do hotel e dicas de entretenimento na area.
Um modelo perfeito para voce que é dono de AirBnB, hotel ou de alguma propriedade para aluguel.""" # REMADE


eletronic_message = """Você Selecionou a  Hotel Loja de Instrumentos em São Paulo / SP, com localização fantasia na rua Líbero Badaró, 282 - Centro Histórico de São Paulo.
Esse assistente tem como objetivo informar e dar assitencia a possiveis clientes e compradores de instrumentos, com base em um catalogo disponilizado a ele, controlando oque esta disponivel, e informações tecnicas para que ele consiga conversar com varios cleintes de varios niveis de experiencia sobre o assunto. Esse modelo pode ser acrescido a serviços adicionias como disponibilizar fotos do estoque e finalizar a venda ao invez de passar para um vendedor humano."""

nutri_message = """Você Selecionou o Nutricionista"""

pizza_message = """Você Selecionou a Pizzaria"""


# Util messages

start_message = """

Para começar a conversa, de um ola!
Caso deseje voltar para o menu principal digite *retornar menu*"""

comercial_extra = """

Caso haja alguma duvida sobre como nós treinamos nossos assistentes, quais informações e documentos são providos para eles, ou duvidas em geral sobre o projeto, orçamentos e soluções particulares, entre em contato no email: joaovictorluz@gmail.com"""

limit_message = lambda max_messages_per_number: f"""Infelizmete voce atingiu o limite de mensagens para o teste diario do programa!
O limite atual é de {max_messages_per_number} pedidos por dia. Espero que tenha gostado da experiencia!"""