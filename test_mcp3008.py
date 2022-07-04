from mcp3008 import MCP3008


adc = MCP3008()
value = adc.read( channel = 0 ) # puedes ajustar el canal en el que lees
print("Read channel 0: %.2f" % (value / 1023.0 * 3.3) )

value = adc.read( channel = 1 ) # puedes ajustar el canal en el que lees

print("Read channel 1: %.2f" % (value / 1023.0 * 3.3) )
