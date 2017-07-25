# bggrss
Board Game Geek Auction Aggregator

# Install Instructions
1. ```cd /usr/share/webapps```
2. ```git clone https://github.com/milogert/bggrss```
3. ```./setup.sh```
4. Install a daemon somehow. Either by:
    1. Copying the contents of ```cron.sh``` to your crontab. Or...
    2. Enabling and starting the ```bggrss.service``` systemd unit.
5. Point your RSS reader at ```/feed.json```
