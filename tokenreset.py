from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(name,seconds):
    s=Serializer('876@#^%jh',seconds)
    return s.dumps({'user':name}).decode('utf-8')
