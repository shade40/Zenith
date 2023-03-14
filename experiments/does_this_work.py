from cleur.markup import markup_spans

buff = ""
for span in markup_spans("[@61]Test [@4]que [@0]test [@7]test"):
    buff += str(span)

    print(repr(span))

print(buff)
