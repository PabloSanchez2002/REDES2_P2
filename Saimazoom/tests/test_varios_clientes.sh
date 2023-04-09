python3 ./launch_controller.py &
pid1=$!
sleep 3
python3 ./launch_robot.py & 
pid2=$!
sleep 3
python3 ./launch_delivery.py &
pid3=$!
sleep 3
echo -e "CLIENTE1\n1\nPRODUCTO1\n1\n" | python3  ./commandline_client.py 2> /dev/null > /dev/null &
sleep 3
echo -e "CLIENTE2\n1\nPRODUCTO2\n2\n" | python3  ./commandline_client.py 2> /dev/null > /dev/null &
sleep 3

sleep 125 #Si no se espera este tiempo y se termina antes el programa será necesario terminar la ejecucion de los python con kill
kill ${pid1}
kill ${pid2}
kill ${pid3}

