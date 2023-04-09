
python3 ./launch_controller.py &
pid1=$!
echo -e "prueba\n1\nproducto\n3\n" | python3  ./commandline_client.py 2> /dev/null  > /dev/null&
python3 ./launch_robot.py & 
pid2=$!
python3 ./launch_delivery.py &
pid3=$!

sleep 65 #este es el tiempo que pueden tardar en total 5 del robot + 20*3 del repartidor
kill ${pid1}
kill ${pid2}
kill ${pid3}