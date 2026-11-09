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
STEEL HOTPOT (?)|1|880#P3
PURAN CRUSHER|Puran Crusher?|2p|1200
1125 TIFIN BOX|Tiffin Box?|1p|2100
OIL KAN 2 LITER|Oil Can 2 Liter|1p|580
oil kan heavy|Oil Can Heavy|1p|480
1 LITER OIL KAN|1 Liter Oil Can|1p|380
KHURBA ADI DISH JEI?|Khurba Dish?|1p|3900
CON-D OIL KAN BIG|Cond Oil Can Big?|8pcs|3900
Milton Flask|Milton Flask|1p|600
KITMANI?|Kitmani? / Kitchen?|1p|350
2 SELF OUNIN IRONY?|2 Self Ironing?|1p|1300
RXZ4 DARBAJET?|8x14 Darbar Jet?|1p|1500
10X14 DARBAJET|10x14 Darbar Jet|1p|1900
CHHADA GIANT|Chhada Giant|2p|1400
NAYARA WATER CLOWER?|Nayara Water Cooler?|1p|1100
Backet|Bucket|1p|1300
Heavy CHHADA BNO?|Heavy Chhada Big?|1p|3500
2nd CHHADA|2nd Chhada|1p|900
1 LITER CHHADA|1 Liter Chhada|1p|400
Silver Water Dechi?|Silver Water Dish?|1p|750?
Steel Glass Set Big 2pcs?|Steel Glass Set Big (2 pcs)|1p|6500
#SMALL (struck through heading, not an item)
TANKI|Tanki|1p|2500
RISE DRAM Heavy?|Rice Drum Heavy?|2p|1000?
Silver Basan|Silver Basan|1p|750?
IONO GLASS LASSI?|10 No. Glass Lassi?|1p|300
GLASS TROY? (struck through)|Glass Tray?|1p|400
30x30 BARTAN GIANT|30x30 Bartan Giant|1p|2600
18x3 Selper GIANT?|18x3 Selper Giant?|1p|1500
550 WATER MEXI GRANDE?|550 Water Mexi Grand?|1p|2800
Silver Chani|Silver Chani|1p|550#P4
MATHAR LAGIAN|Mathar Lagan (metal tray/plate)|1p|950
MATHAR DHAI|Mathar Dhari|5pr|7000
Silver LIDDEL|Silver Liddel|1p|550
Silver KARUGIR|Silver Karugir|1p|750
Silver BABUNA F2x86|Silver Babuna (size notation unclear)|1p|34980
Hopis PAPER KAJET|Hopis Paper Kajet|1p|5500
Silver TEHI|Silver Tethi|1p|900
5NO JAHRA|5 No. Jahra|5no|100
Ravi Soup Plate|Ravi Soup Plate|12p|1100
VILANI|Vilani|1p|90
3pcs NAYASA HOIPOI|3 pcs Nayasa Hoipoi|1p|2800
6 pinte Ptuy cooker|6 pint Pressure Cooker|1p|900
5 liter cooker|5 Litre Cooker|1p|1400
10 liter cooker|10 Litre Cooker|1p|3000
1No SANITROTIFFIN|1 No. Sanitary Tiffin|1p|480
4 pinte Ptuy cooker|4 pint Pressure Cooker|1p|600
JOSECHANI|Josechani|1p|300
Spone Pattic|Spoon Plastic|1p|150
MURKUL SACHAA|Murkul Sachaa|1p|480