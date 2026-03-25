"""
Management command: popula o glossário com termos iniciais do setor têxtil.

Uso:
    python manage.py seed_glossario
    python manage.py seed_glossario --clear   # limpa e repopula
"""
from django.core.management.base import BaseCommand

from apps.transcricao.models import GlossarioTermo

TERMOS_INICIAIS = [
    # Tecelagem
    ('urdidura', 'tecelagem', ['urdidúra', 'urdidura', 'ardidura', 'urdedura'], 'Conjunto de fios longitudinais no tecido'),
    ('trama', 'tecelagem', ['trama', 'trama', 'tramas'], 'Fios transversais que se entrelaçam com a urdidura'),
    ('urdimento', 'urdimento', ['urdimento', 'urdismento', 'ordimento'], 'Processo de preparação dos fios de urdidura'),
    ('tear', 'tecelagem', ['tear', 'tiar'], 'Máquina de tecer'),
    ('liçateira', 'tecelagem', ['liçateira', 'lissateira', 'liçadeira'], 'Peça do tear que guia os fios'),
    ('pente', 'tecelagem', ['pente', 'penite'], 'Elemento do tear que compacta a trama'),
    ('lançadeira', 'tecelagem', ['lançadeira', 'lansadeira', 'lançadéra'], 'Dispositivo que carrega o fio de trama'),
    ('remetagem', 'tecelagem', ['remetagem', 'remetagen', 'remettagem'], 'Passagem dos fios pelo liço'),
    ('liço', 'tecelagem', ['liço', 'liçu', 'liso'], 'Quadro do tear que movimenta fios de urdidura'),
    ('calada', 'tecelagem', ['calada', 'colada'], 'Abertura entre fios de urdidura para passagem da trama'),

    # Malharia
    ('malharia', 'malharia', ['malharia', 'malheria'], 'Setor de fabricação de tecidos de malha'),
    ('malha', 'malharia', ['malha', 'maia'], 'Tecido feito por entrelaçamento de laçadas'),
    ('jersey', 'malharia', ['jersey', 'jérssei', 'gersei'], 'Tipo de malha simples'),
    ('ribana', 'malharia', ['ribana', 'rebana', 'ribanna'], 'Malha elástica usada em barras e punhos'),
    ('moletom', 'malharia', ['moletom', 'moletão', 'moletão'], 'Tecido de malha com pelo interno'),
    ('interlock', 'malharia', ['interlock', 'interlok', 'intelok'], 'Malha dupla de alta estabilidade'),

    # Acabamento
    ('amaciamento', 'acabamento', ['amaciamento', 'amaciamento', 'amansamento'], 'Processo de suavização do tecido'),
    ('ramagem', 'acabamento', ['ramagem', 'ramagen'], 'Processo de estabilização dimensional em rama'),
    ('rama', 'acabamento', ['rama', 'ramma'], 'Máquina de acabamento que estica e seca o tecido'),
    ('sanforização', 'acabamento', ['sanforização', 'sanforissação'], 'Processo de pré-encolhimento do tecido'),
    ('mercerização', 'acabamento', ['mercerização', 'mercerissação'], 'Tratamento com soda cáustica para brilho'),
    ('calandragem', 'acabamento', ['calandragem', 'calandragen'], 'Processo de prensagem para brilho e toque'),
    ('esmerilagem', 'acabamento', ['esmerilagem', 'esmerilagem', 'esmerillagem'], 'Processo de levantamento de pelo no tecido'),
    ('chamuscagem', 'acabamento', ['chamuscagem', 'chamuscagen'], 'Queima de fibras soltas da superfície'),

    # Tinturaria
    ('tinturaria', 'tinturaria', ['tinturaria', 'tintoraria', 'tenturaria'], 'Setor de tingimento'),
    ('tingimento', 'tinturaria', ['tingimento', 'tingimento', 'tinjimento'], 'Processo de aplicação de cor ao tecido'),
    ('estamparia', 'tinturaria', ['estamparia', 'estamperia'], 'Processo de impressão de estampas'),
    ('alvejamento', 'tinturaria', ['alvejamento', 'alvejamento'], 'Branqueamento do tecido'),
    ('jigger', 'tinturaria', ['jigger', 'jiger', 'giger'], 'Máquina de tingimento por esgotamento'),
    ('autoclave', 'tinturaria', ['autoclave', 'ato clavo', 'autoclavi'], 'Equipamento de tingimento sob pressão'),
    ('corante', 'tinturaria', ['corante', 'corant'], 'Substância usada para tingir'),
    ('solidez', 'qualidade', ['solidez', 'solidês'], 'Resistência da cor à lavagem e luz'),

    # Fios e fibras
    ('fio', 'tecelagem', ['fio', 'fi'], 'Elemento básico de produção têxtil'),
    ('título', 'qualidade', ['título', 'titolo'], 'Medida de espessura do fio (Ne, Nm, Tex)'),
    ('torção', 'tecelagem', ['torção', 'torsão', 'torsão'], 'Número de voltas por metro no fio'),
    ('fiação', 'tecelagem', ['fiação', 'fiassão'], 'Processo de transformação de fibras em fios'),
    ('poliéster', 'tecelagem', ['poliéster', 'poliester', 'poliéter'], 'Fibra sintética mais usada no setor'),
    ('viscose', 'tecelagem', ['viscose', 'viscozi'], 'Fibra artificial de celulose regenerada'),
    ('elastano', 'malharia', ['elastano', 'elástano', 'lastano'], 'Fibra elástica (spandex/lycra)'),
    ('algodão', 'tecelagem', ['algodão', 'algodão', 'algodão'], 'Fibra natural mais usada no setor'),

    # Qualidade e gestão
    ('lote', 'gestao', ['lote', 'loti'], 'Conjunto de produção de mesma referência'),
    ('refugo', 'qualidade', ['refugo', 'refúgo', 'refujo'], 'Peça com defeito descartada da produção'),
    ('segunda qualidade', 'qualidade', ['segunda qualidade', 'segunda'], 'Peça com pequeno defeito, vendida com desconto'),
    ('gramatura', 'qualidade', ['gramatura', 'gramatoora', 'gramatúra'], 'Peso do tecido em g/m²'),
    ('toque', 'qualidade', ['toque', 'toki'], 'Sensação tátil do tecido (macio, áspero, etc.)'),
    ('metragem', 'gestao', ['metragem', 'metragem', 'metragen'], 'Quantidade em metros de tecido'),
    ('rolão', 'gestao', ['rolão', 'rolo', 'rolhão'], 'Rolo de tecido acabado'),
    ('ficha técnica', 'gestao', ['ficha técnica', 'ficha tecnica'], 'Documento com especificações do produto'),
    ('pcp', 'gestao', ['pcp', 'pecepê'], 'Planejamento e Controle da Produção'),
    ('setup', 'manutencao', ['setup', 'set up', 'cete ap'], 'Preparação/regulagem de máquina para nova produção'),
    ('manutenção preventiva', 'manutencao', ['manutenção preventiva', 'preventiva'], 'Manutenção programada para evitar falhas'),
    ('eficiência', 'gestao', ['eficiência', 'eficiência', 'eficiencia'], 'Percentual de produção real vs. meta'),
]


class Command(BaseCommand):
    help = 'Popula o glossário com termos têxteis iniciais'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Limpa o glossário antes de inserir')

    def handle(self, *args, **options):
        if options['clear']:
            count = GlossarioTermo.objects.count()
            GlossarioTermo.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Glossário limpo ({count} termos removidos).'))

        criados = 0
        ignorados = 0
        for termo, categoria, variantes, descricao in TERMOS_INICIAIS:
            _, created = GlossarioTermo.objects.get_or_create(
                termo_correto=termo,
                defaults={
                    'categoria': categoria,
                    'variantes': variantes,
                    'descricao': descricao,
                    'ativo': True,
                }
            )
            if created:
                criados += 1
            else:
                ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Glossário populado: {criados} termos criados, {ignorados} já existiam.'
        ))
