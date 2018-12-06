import click
import sys
import os

envvar = ['RECAST_AUTH_USERNAME', 'RECAST_AUTH_PASSWORD']

@click.group()
def auth():
    pass


@auth.command()
def setup():
    expt = 'ATLAS'
    if sys.stdout.isatty():
        click.secho('Sorry, we will not print your password to stdout. Use `eval $(recast auth setup)` to store your credentials in env variables', fg = 'red')
        raise click.Abort()

    username = click.prompt('Enter your username to authenticate as {}'.format(expt), hide_input = False, err = True)
    password = click.prompt('Enter your password for {} (VO: {})'.format(username,expt), hide_input = True, err = True)

    click.secho("export {}='{}'".format(envvar[0],username))
    click.secho("export {}='{}'".format(envvar[1],password))
    click.secho('You password is stored in the environment variable {}. Unset to clear your password. Or exit the shell.'.format(' and '.join(envvar)), err = True)

@auth.command()
@click.option('--basedir', default = None)
def write(basedir):
    basedir = basedir or os.getcwd()
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    krbfile = os.path.join(basedir,'getkrb.sh')
    with open(krbfile,'w') as f:
        f.write('echo '{}'|kinit {}@CERN.CH'.format(
            os.environ[envvar[1]],os.environ[envvar[0]]
            )
        )
    os.chmod(krbfile, 0o755)
    authlocvar = 'PACKTIVITY_AUTH_LOCATION'
    click.secho('export {}={}'.format(authlocvar,os.path.abspath(basedir)))

        

@auth.command()
def destroy():
    if sys.stdout.isatty():
        click.secho('Use eval $(recast auth destroy) to unset the variables', fg = 'red')
        raise click.Abort()
    click.secho('unset {}'.format(envvar[0]))
    click.secho('unset {}'.format(envvar[1]))