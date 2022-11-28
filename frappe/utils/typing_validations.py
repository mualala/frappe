from inspect import _empty, isclass, signature
from typing import Callable, ForwardRef, Sequence, Union


def qualified_name(obj) -> str:
	"""
	Return the qualified name (e.g. package.module.Type) for the given object.

	Builtins and types from the :mod:`typing` package get special treatment by having the module
	name stripped from the generated name.

	"""
	discovered_type = obj if isclass(obj) else type(obj)
	module, qualname = discovered_type.__module__, discovered_type.__qualname__

	if module == "typing":
		return obj
	elif module in {"types", "builtins"}:
		return qualname
	else:
		return f"{module}.{qualname}"


def validate_argument_types(func: Callable, args: tuple, kwargs: dict):
	"""
	Validate the types of the arguments passed to a function with the type annotations
	defined on the function.

	"""
	if annotations := func.__annotations__:
		# generate kwargs dict from args
		arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]
		arg_values = args or func.__defaults__ or []
		prepared_args = dict(zip(arg_names, arg_values))
		prepared_args.update(kwargs)

		# check if type hints dont match the default values
		func_signature = signature(func)
		func_params = dict(func_signature.parameters)

		# check if the argument types are correct
		for current_arg, current_arg_type in annotations.items():
			if current_arg not in prepared_args:
				continue

			current_arg_value = prepared_args[current_arg]

			# if the type is a ForwardRef or str, ignore it
			if isinstance(current_arg_type, (ForwardRef, str)):
				continue

			if isinstance(current_arg_type, Sequence):
				current_arg_type = tuple(
					x for x in current_arg_type.__args__ if not isinstance(x, (ForwardRef, str))
				)

			param_def = func_params.get(current_arg)

			if param_def.default is not _empty:
				if isinstance(current_arg_type, tuple):
					if param_def.default not in current_arg_type:
						current_arg_type += (type(param_def.default),)
				elif param_def.default != current_arg_type:
					current_arg_type = Union[current_arg_type, type(param_def.default)]

			if not isinstance(current_arg_value, current_arg_type):
				raise TypeError(
					f"Argument '{current_arg}' must be of type '{qualified_name(current_arg_type)}' but got '{qualified_name(current_arg_value)}'"
				)
