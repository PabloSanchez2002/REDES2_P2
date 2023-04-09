python3 ./launch_controller.py &
pid1=$!
echo -e "prueba\n2\n" | python3  ./commandline_client.py 2> /dev/null  
pid2=$!

kill -s 9 $pid1
kill -s 9 $pid2