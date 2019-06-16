Example crontab being used to grab images from 2 cameras:

`*/5 * * * * /usr/bin/python /var/www/public_html/uvcsnapshot.py -x 5 -i 7 -c camerahostname.com:8443 -u username -p password -o /var/www/public_html/back_cam`

`2-59/5 * * * * /usr/bin/python /var/www/public_html/uvcsnapshot.py -x 5 -i 13 -c camerahostname.com:443 -u username -p password -o /var/www/public_html/front_cam`

This cronjob runs the  uvcsnapshot.py script every 5 minutes (starting at the 0'th minute for the back cam, and the 2nd minute for the fromt cam). Every 7s for the back cam, it grabs an image from the camera. Every 13s it grabs one from the front camera. The first image it grabs it stores in the archive (meaning, every 5 minutes a new image is archived). This gives us a relatively real time "live" view and a reasonable 5min archive interval.

The times are staggered to limit impact on upstream by minimizing overlapping times when both cameras are sending an image at the same time, as this site has a crappy cable connection.