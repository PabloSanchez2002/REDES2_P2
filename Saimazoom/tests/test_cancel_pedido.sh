#La recomendación para este test es ejecutar primero:
#python3 launch_controller cleanDB
#De esta forma se borrará la base de datos y funcionará todo correctamente
#Si no se ejecuta antes intentará hacer un cancel de un pedido que ya ha sido entregado


python3 ./launch_controller.py &
sleep 3
pid1=$!
echo -e "prueba\n1\nproducto\n3\n3\n1\n2" | python3  ./commandline_client.py 2> /dev/null  &
sleep 3
kill ${pid1}