import click, os

def run(port:int):
    os.popen("cd /pbf && nohup python fabot.py {} > /dev/null 2>&1 &".format(port))
    click.echo("run server on port:{}".format(port))

def kill(port:int):
    data = os.popen("lsof -i:{}".format(port)).read().split("\n")[1:-1]
    for i in data:
        i = i.lstrip().rstrip()
        if len(i) != 0:
            i = i.split()[1]
            os.popen("kill -9 {}".format(i))
            click.echo("killed pid:{} on port:{}".format(i, port))

@click.group()
def cli():
    pass

@click.command()
@click.argument("port", nargs=-1)
def start(port):
    '''
    Run server(s) on :PORT:\n
    When user gives 1 port, it only run server on that port.\n
    When user gives 2 ports, it will run servers on range(port).\n
    When user gives 3 or more ports, it will run servers on all the ports.\n
    '''
    
    if not len(port):
        click.secho("Please give at least one port!", fg="red", bg="yellow")
    elif len(port) == 1:
        run(int(port[0]))
        click.secho("Successfully ran server on {}".format(port[0]), fg="green", bg="yellow")
    elif len(port) == 2:
        port1 = int(port[0])
        port2 = int(port[1])
        if port1 < port2:
            for i in range(port1, port2+1):
                run(i)
        else:
            for i in range(port2, port1+1):
                run(i)
        click.secho("Successfully ran server on {} to {}".format(port1, port2), fg="green", bg="yellow")
    else:
        for i in port:
            run(int(i))
        click.secho("Successfully ran server on {}".format(port), fg="green", bg="yellow")

@click.command()
@click.argument("port", nargs=-1)
def stop(port):
    '''
    Stop server(s) which on :PORT:\n
    When user gives 1 port, it only kill server on that port.\n
    When user gives 2 ports, it will kill servers on range(port).\n
    When user gives 3 or more ports, it will kill servers on all the ports.\n
    '''
    
    if not len(port):
        click.secho("Please give at least one port!", fg="red", bg="yellow")
    elif len(port) == 1:
        kill(int(port[0]))
        click.secho("Successfully killed server on {}".format(port[0]), fg="green", bg="yellow")
    elif len(port) == 2:
        port1 = int(port[0])
        port2 = int(port[1])
        if port1 < port2:
            for i in range(port1, port2+1):
                kill(i)
        else:
            for i in range(port2, port1+1):
                kill(i)
        click.secho("Successfully killed server on {} to {}".format(port1, port2), fg="green", bg="yellow")
    else:
        for i in port:
            kill(int(i))
        click.secho("Successfully killed server on {}".format(port), fg="green", bg="yellow")

@click.command()
def restart():
    """
    Restart all servers
    """
    portList = []
    data = os.popen("lsof -i").read().split("\n")[1:-1]
    for i in data:
        i = i.lstrip().rstrip()
        if len(i) != 0 and "*:" in i.split()[8]:
            port = int(i.split()[8].replace("*:", ""))
            if port not in portList and port != 1020:
                kill(port)
                run(port)
                portList.append(port)
    click.secho('Successfully restarted all the servers', fg="green", bg="yellow")

@click.command()
@click.option("--port", help="The port which run web control.", default=1020, type=int)
def serve(port):
    """
    Run web control panel on :PORT(1020):
    """
    os.popen("cd /pbf/pbf_tools && nohup python panel.py {} > /dev/null 2>&1 &".format(port))
    click.secho('Successfully run web panel on port:{}'.format(port), fg="green", bg="yellow")

cli.add_command(start)
cli.add_command(stop)
cli.add_command(restart)
cli.add_command(serve)

if __name__ == "__main__":
    cli()