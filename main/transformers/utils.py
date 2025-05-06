from schema import Schema, And, Use, Optional, SchemaError


def check(conf_schema, conf):
    try:
        conf_schema.validate(conf)
        return True
    except SchemaError:
        return False


conf_schema = Schema({
    'version': And(Use(int)),
    'info': {
        'conf_one': And(Use(float)),
        'conf_two': And(Use(str)),
        'conf_three': And(Use(bool)),
        Optional('optional_conf'): And(Use(str))
    }
})

conf = {
    'version': 1,
    'info': {
        'conf_one': 2.5,
        'conf_two': 'foo',
        'conf_three': False,
        'optional_conf': 'bar'
    }
}

print(check(conf_schema, conf))
