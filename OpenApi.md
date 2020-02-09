# Open Api

Host: `https://explorer.newtonproject.org`

Url prefix: `/api/v{version_number}`, current version number is `3`.

* Get Transaction By Hash

    * url:  `/transaction`

    * request method:  `GET`

    * params:

    |Field | Type | Desc |
    |:-:|:-:|:-:|
    |txid| String | Transaction Hash |

* Get Transactions By Address

    * url:  `/transactions`

    * request method:  `GET`

    * params:

    |Field | Type | Desc |
    |:-:|:-:|:-:|
    | limit | int | Page limit |
    | address | String | Wallet Address |
    | pageNum | int | query page number |
    | category | String | `send` is filter by send transactions, `receive` is filter by receive transactions, default is `all` |