import inspect
import json
import os
import sys
from typing import Union, get_type_hints

import click
from dotenv import load_dotenv

from av_cli import __version__


def _python_type_to_click(param_type):
    """Map a Python type hint to a Click type."""
    if param_type == bool or param_type == 'bool':
        return bool
    if param_type == int or param_type == 'int':
        return click.INT
    if param_type == float or param_type == 'float':
        return click.FLOAT
    # Handle Optional[X]
    if hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
        args = param_type.__args__
        if len(args) == 2 and type(None) in args:
            inner = args[0] if args[1] is type(None) else args[1]
            return _python_type_to_click(inner)
    return click.STRING



def _make_tool_command(func, tool_name):
    """Build a Click command for a single tool function."""
    from av_api.registry import extract_description

    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    # Build short option flags, skipping conflicts with -h (help) and -k (api-key)
    used_shorts = {'h', 'k'}
    short_map = {}
    for pname in sig.parameters:
        for ch in pname.lower():
            if ch.isalpha() and ch not in used_shorts:
                used_shorts.add(ch)
                short_map[pname] = f'-{ch}'
                break

    # Check if function has a 'symbol' parameter
    has_symbol = 'symbol' in sig.parameters and sig.parameters['symbol'].default is inspect.Parameter.empty

    params = []
    # Add --api-key/-k to each subcommand so it can appear after the command name
    params.append(
        click.Option(
            ['--api-key', '-k'],
            envvar=['ALPHAVANTAGE_API_KEY', 'ALPHA_VANTAGE_API_KEY'],
            help='Alpha Vantage API key (required)',
            is_eager=True,
            expose_value=True,
        )
    )
    # Add optional positional argument for symbol (e.g., av-cli global_quote AAPL)
    if has_symbol:
        params.append(
            click.Argument(['_symbol'], required=True, metavar='SYMBOL')
        )
    for pname, param in sig.parameters.items():
        # Skip symbol as option — it's handled by positional argument
        if pname == 'symbol' and has_symbol:
            continue
        ptype = hints.get(pname, str)
        click_type = _python_type_to_click(ptype)
        short = short_map.get(pname)

        if click_type is bool:
            params.append(
                click.Option(
                    [f'--{pname}/--no-{pname}'],
                    default=param.default if param.default is not inspect.Parameter.empty else False,
                    help=f'{pname} flag',
                )
            )
        else:
            required = param.default is inspect.Parameter.empty
            decls = [f'--{pname}']
            if short:
                decls.append(short)
            params.append(
                click.Option(
                    decls,
                    type=click_type,
                    required=required,
                    default=None if required else param.default,
                    help=pname,
                )
            )

    def callback(**kwargs):
        from av_api.context import set_api_key

        local_api_key = kwargs.pop('api_key', None)
        ctx = click.get_current_context()
        api_key = local_api_key or ctx.obj.get('api_key') or os.getenv('ALPHAVANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            click.echo('Error: API key required. Set ALPHAVANTAGE_API_KEY or use -k. Get a free key at https://www.alphavantage.co/support/#api-key', err=True)
            sys.exit(1)

        # Map positional _symbol to symbol kwarg
        if has_symbol:
            kwargs['symbol'] = kwargs.pop('_symbol', None)
            if not kwargs['symbol']:
                click.echo('Error: SYMBOL is required. Usage: av-cli <command> AAPL', err=True)
                sys.exit(1)

        set_api_key(api_key)
        result = func(**kwargs)

        if isinstance(result, str):
            click.echo(result)
        else:
            click.echo(json.dumps(result, indent=2, default=str))

    cmd = click.Command(
        name=tool_name,
        callback=callback,
        params=params,
        help=extract_description(func),
    )
    return cmd


class ToolGroup(click.Group):
    """Click group that lazily loads tool commands from the registry."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tools_loaded = False

    def _load_tools(self):
        if self._tools_loaded:
            return
        self._tools_loaded = True

        from av_api.registry import _all_tools_registry, ensure_tools_loaded

        ensure_tools_loaded()

        # Skip utility/internal tools not meant for CLI usage
        _SKIP_TOOLS = {'ping', 'add_two_numbers', 'search', 'fetch'}

        for func in _all_tools_registry:
            name = func.__name__
            if name in _SKIP_TOOLS:
                continue
            cmd = _make_tool_command(func, name)
            self.add_command(cmd)

    def list_commands(self, ctx):
        self._load_tools()
        return super().list_commands(ctx)

    def get_command(self, ctx, cmd_name):
        self._load_tools()
        return super().get_command(ctx, cmd_name.lower())


@click.group(cls=ToolGroup, context_settings=dict(
    help_option_names=['-h', '--help'],
    max_content_width=200,
))
@click.version_option(version=__version__, prog_name="av-cli")
@click.option('--api-key', '-k', envvar=['ALPHAVANTAGE_API_KEY', 'ALPHA_VANTAGE_API_KEY'], hidden=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, api_key, verbose):
    """Alpha Vantage CLI - direct access to all Alpha Vantage API.

    \b
    Quick start:
      1. Get a free API key at https://www.alphavantage.co/support/#api-key
      2. export ALPHAVANTAGE_API_KEY=your_key
      3. av-cli global_quote AAPL
    Or use -k for single use: av-cli global_quote AAPL -k your_key
    """
    load_dotenv(os.path.join(os.getcwd(), '.env'))
    ctx.ensure_object(dict)
    ctx.obj['api_key'] = api_key
    ctx.obj['verbose'] = verbose


if __name__ == "__main__":
    cli()
