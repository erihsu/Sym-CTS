#!/usr/bin/perl


use Getopt::Std;

$inFile = $ARGV[1];
die "ERROR missing input file," unless(-f $inFile);
open INFILE, "$inFile";

# Opening output files
open (MAINFILE, '>data.plot');
open (NODESFILE, '>nodes.plot');
open (SINKSFILE, '>sinks.plot');
open (BUFFERSFILE, '>buffers.plot');
open (BLOCKFILE, '>block.plot');


#process configuration file first

while(<INFILE>){
  if(/^\s*num\s+sink\s+(\d+)\s*$/){
      $count = $1;
      print "$_\n";
      for $i (0 .. ($count - 1)) {
         $_ = <INFILE>;
         die "ERROR" unless(/^\s*(\d+)\s+(\S+)\s+(\S+)\s+\S+\s*$/);
	 $sinkmap_x{$1} = $2;
	 $sinkmap_y{$1} = $3;
	 if($i == 0){
	    $maxx = $2;
	    $maxy = $3;
	 } else {
	    if($maxx < $2){$maxx=$2;}
	    if($maxy < $3){$maxy=$3;}
	 }
      }
   }
  if(/^\s*num\s+blockage\s+(\d+)\s*$/){
    $numBlockage = $1;
    for $i (0 .. ($numBlockage - 1)) {
      $_ = <INFILE>;
      die "ERROR" unless(/^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$/);
      print BLOCKFILE "$1 $2\n";
      print BLOCKFILE "$3 $2\n";
      print BLOCKFILE "$3 $4\n";
      print BLOCKFILE "$1 $4\n";
      print BLOCKFILE "$1 $2\n";
      print BLOCKFILE "$3 $4\n";
      print BLOCKFILE "$1 $4\n";
      print BLOCKFILE "$3 $2\n\n";
    }
  }
}
close INFILE;


$inFile = $ARGV[0];
die "ERROR missing input file," unless(-f $inFile);
open INFILE, "$inFile";
#my @wirelist;
while(<INFILE>){
   if(/^\s*sourcenode\s+(\d+)\s+(\d+)\s*$/){
   	$nodes_x{0} = $1;
	$nodes_y{0} = $2;
	push @bufferlist, $1;
 	push @bufferlist, $2;
	push @bufferlist, 1;
  }
   if(/^\s*num\s+buffer\s+(\S+)\s*$/){
      $count = $1;
      print "$_\n";
      for $i (0 .. ($count - 1)) {
         $_ = <INFILE>;
         die "ERROR" unless(/^\s*(\d+)\s+(\d+)\s+(\d+)\s*$/);
	 push @bufferlist, $1; 
	 push @bufferlist, $2;
	 push @bufferlist, $3; 
      }
   }

   if(/^\s*num\s+node\s+(\d+)\s*$/){
      $count = $1;
      print "$_\n";
      for $i (0 .. ($count - 1)) {
         $_ = <INFILE>;
         die "ERROR" unless(/^\s*(\d+)\s+(\S+)\s+(\S+)\s*$/);
	 if($maxx < $2){$maxx=$2;}
	 if($maxy < $3){$maxy=$3;}
	 $nodes_x{$1} = $2;	 
	 $nodes_y{$1} = $3;
	 print NODESFILE "$2 \t $3\n";
      }
   }

   if(/^\s*num\s+wire\s+(\d+)\s*$/){
      $count = $1;
      print "$_\n";
      for $i (0 .. ($count - 1)) {
         $_ = <INFILE>;
         die "ERROR" unless(/^\s*(\d+)\s+(\S+)\s+(\S+)\s*$/);
	 push @wirelist,$1;
	 push @wirelist,$2;
	 push @wirelist,$3;
      }
   }

   if(/^\s*num\s+sinknode\s+(\d+)\s*$/){
      $count = $1;
      print "$_\n";
      for $i (0 .. ($count - 1)) {
         $_ = <INFILE>;
         die "ERROR" unless(/^\s*(\d+)\s+(\S+)\s*$/);
	 $nodes_x{$1} = $sinkmap_x{$2};
	 $nodes_y{$1} = $sinkmap_y{$2};
	 print SINKSFILE "$sinkmap_x{$2} \t $sinkmap_y{$2}\n";
      }
   }

}

# Opening output file

$maxx = $maxx*1.1;
$maxy = $maxy*1.1;
print MAINFILE "set xrange [0:$maxx]\n";
print MAINFILE "set yrange [0:$maxy]\n";
print MAINFILE "set style arrow 1 nohead lt 3\n";
print MAINFILE "set terminal x11\n";


while($#wirelist > 0){
   ($in,$out,$model) = @wirelist;
   @wirelist = @wirelist[(3..$#wirelist)];
   print MAINFILE "set arrow from $nodes_x{$in},$nodes_y{$in} to $nodes_x{$out},$nodes_y{$out} as 1\n";
}

while($#bufferlist > 0){
   ($in,$out,$model) = @bufferlist;
   @bufferlist = @bufferlist[(3..$#bufferlist)];
   print BUFFERSFILE "$nodes_x{$in} \t $nodes_y{$in}\n";
}

print MAINFILE "plot \"nodes.plot\" notitle with points pointtype 3 pointsize 1 linetype 3, \"sinks.plot\" notitle with points pointtype 13 pointsize 2 linetype 16, \"buffers.plot\" notitle with points pointtype 13 pointsize 3 linetype 3, \"block.plot\" notitle w l lw 2 lt rgb \"black\"\n"; 


close MAINFILE;
close NODESFILE;
close SINKSFILE;
close BUFFERSFILE;
close BLOCKFILE;

close INFILE;


system "gnuplot -persist < data.plot";
