# This script is used to generate lookup table of clock buffer using Hspice.

# The lookup table considering input slew, output load and input slew polarity(rising or fall).
# Output slew, delay and their standard-variance(std) can be look-up from this table.

# The technology file under library/tech folder will be used as mosfet parameter file.

# After excuation, new buffer model and lookup table will be generated under library/spice and library/lib respectively.