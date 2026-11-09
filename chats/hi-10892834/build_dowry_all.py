import re
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

# Format per line: as_written|qty|price   (? = uncertain reading)
RAW = """
#P1
Soup Plate|12pcs|1700
Sweet Bowl|12pcs|1100
Sweet Plate|12pcs|1080
Tea Spoon|12p|280
Rice Dish|2p|1100
Rice Spoon|2p|180
Half Bowl|1p|450?
6 no ...|2p?|440
5 no ...|1p?|680
Spoon|1p?|900
Tea Glass|12p|1100
Water Glass|12p|1300
Tea Cup|12p|180
Soup Box|1p|550
Aicka|1p|380
Puri Dabba|1p|750
Clip Tiffin Box|1p|300
9 no Lotha|1p|480
1 no Lotha|1p|750
12 no Lotha|2p|200
Hot Pring?|2p?|200
4pcs Jug|4pcs|2200
4KA Priyapot?|1p|790?
Pankutti?|1p|1100
Chhada Stand?|2p|740?
Soupan|1p|480
Juse Chani?|2p|760
3no Tray|1p|480
4no Tray|1p|550
Steel Tray?|1p|750?
#P2
MANDI THALA|1|750
LIDDEL (?)|1|280
SURMADANI|2|380
JAHRA|1|280
TEA CHANI|1|110
ULIANI|1|180
SPONE LATLI (?)|1|180
STEEL HANDLE (?) (struck through)|1|380
NON-STICK TAWA|1|900
THIRKI (?)|2|100
OIL PALI|1|110
BAGIARPAN (?)|1|180
SERVING LONG (?)|1|210
TALANI (?)|1|180
PAPER CHUMHA (?)|1|210
TEA DONHA (?)|1|180
WATER DONHA (?)|1|380
CHANA TAHRA (?)|1|180
GIRDAR BALIAN (?)|2|780?
LEMON SUZAR (?)|1|210
GLASS LATER (?)|1|150
MOOMY VISKAR (?)|1|140
SILVER TAVA (?)|1|450
OUNIN MASHER (?)|1|180
MANSI CHANINO (?)|1|700?
9NO KADAI (?)|1|900
HEAVY BAGANPUR BIG (?)|1|750?
HEAVY BALANPUR SMALL (?)|1|480
DHOOM GLASS STAND (?)|1|600
STEEL HOTPOT (?)|1|880