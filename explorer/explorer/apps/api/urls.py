from django.conf.urls import patterns, include, url

urlpatterns = patterns('api.apis',
                       # system
                        url(r'^system/ping/$',                     'api_ping'),
                        url(r'^system/ip/$',                       'api_get_ip'),
                        url(r'^peer/$',                             'api_get_peer'),
		                # block chain
                        url(r'^version/$',                         'api_show_version'),
                        url(r'^blocks/$',                          'api_show_blocks'),
                        url(r'^block-index/(?P<height>[0-9]+)/$', 'api_show_block_info_by_height'),
                        url(r'^block/(?P<blockhash>[0-9a-z]+)/$', 'api_show_block_info'),
                        # transaction
                        url(r'^txs/$',                             'api_show_transactions'),
                        url(r'^tx/send/$',          'api_send_transcation'),
                        url(r'^tx/(?P<txid>[0-9a-z]+)/$',          'api_show_transaction'),
                        # address
                        url(r'^addr/(?P<addr>[0-9a-zA-Z]+)/$',          'api_show_addr_summary'),
                        
                        url(r'^addrs/txs/$',          'api_show_transactions_by_addresses'),
                        url(r'^addrs/(?P<addrs>[0-9a-zA-Z,]+)/txs/$',          'api_show_transactions_by_addresses'),
                        # new tx, block
                        url(r'^newtx/$',          'api_show_newtx'),
                        url(r'^newblock/$',          'api_show_newblock'),
                        # misc
                        url(r'^sync/$',                            'api_get_sync'),
                        url(r'^status/$',                          'api_get_status'),
                        url(r'^currency/$',                        'api_get_currency'),
                        url(r'^utils/estimatefee/$',               'api_get_estimatefee'),

                        # for mobile client
                        url(r'^transactions/$', 'api_show_client_transactions'),
                        url(r'^transaction/$', 'api_show_client_transaction'),
                        url(r'^contracts_list/$', 'api_show_contracts_list'),
                        url(r'^contract/(?P<contractAddr>[0-9a-zA-Z]+)/$', 'api_show_contract'),
            )


