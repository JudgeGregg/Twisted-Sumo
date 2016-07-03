ESSID=`iw dev wlp0s20u7 scan | grep SSID | grep Sumo | cut -d ' ' -f 2`
echo $ESSID
iw dev wlp0s20u7 connect $ESSID
ip addr add 192.168.2.3/24 dev wlp0s20u7
