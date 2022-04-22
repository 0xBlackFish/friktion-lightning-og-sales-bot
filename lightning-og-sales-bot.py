import requests
import pandas as pd
from datetime import datetime, timedelta
from discord_webhook import DiscordEmbed, DiscordWebhook
import os


# read webhook url from the environment
webhook_url = os.getenv('DISCORD_WEBHOOK_LOG')


# read-in transaction data from magic eden
url = "https://api-mainnet.magiceden.dev/v2/collections/lightning_ogs/activities?offset=0&limit=100"

payload={}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

df = pd.DataFrame(response.json())


# Convert unix time to datetime
df['date'] = df['blockTime'].apply(lambda x: datetime.fromtimestamp(x))


# Limit to purchases only within the last hour
df_sales_last_hour = df[(df['type'] == 'buyNow') & (df['date'] > datetime.now() - timedelta(minutes=5))]


if df_sales_last_hour.empty:
    print(datetime.now(), 'No Lightning OGs have been sold in the last hour...')
    pass

else:

    for index, log in df_sales_last_hour.iterrows():

        # establish webhook
        webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True)

        # create embed object for webhook
        embed = DiscordEmbed(title='Lightning OG Sales Alert', color='5856d6')
        
        # create embed description
        embed.set_description("**Transaction ID:** [{0}](https://solscan.io/tx/{0})".format(log['signature']))

        # add fields to embed
        embed.add_embed_field(name='Time', value="{} UTC".format(log['date'].strftime('%Y-%m-%d %H:%M:%S')), inline=False)
        embed.add_embed_field(name='Buyer', value=log['buyer'], inline=False)
        embed.add_embed_field(name='Seller', value=log['seller'],inline=False)
        embed.add_embed_field(name='Price', value="{} SOL".format(log['price']),inline=False)

        # add embed object to webhook
        webhook.add_embed(embed)

        response = webhook.execute()