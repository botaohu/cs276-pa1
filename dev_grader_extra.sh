#!/bin/bash
fmt="user = %U, system = %S, elapsed = %e, memory = %M, memory = %K"

queryin=dev_queries
queryref=dev_output
corpus=data

out=output/outputextra
if [ ! -d "$out" ]; then
  mkdir -p $out
fi
index=$out/index
queryout=$out/query_out_dev
querytime=$out/query_out_dev/querytime.txt
query_memout=$out/query_out_dev/query_memory_out
if [ ! -d "$queryout" ]; then
  mkdir -p $queryout
fi

echo "" >&2
echo "###### Testing Retrieval ######" >&2
START=$(date +%s)
query_error=0
echo  > $querytime
for i in {1..8}
do
./memusg -o $query_memout ./extra_credit/query.sh $index < $queryin/query.${i} > $queryout/${i}
END=$(date +%s)
DIFF=$(( $END - $START ))
echo "$DIFF seconds" >> $querytime

query_diff=`diff -U 0 $queryout/${i} $queryref/${i}.out | grep -v ^@ | wc -l`
if [ $query_diff -gt 0 ]; then
  query_error=`expr $query_error + 1`
  echo "${i}"
fi
done
echo "######"
if [ $query_error -gt 0 ]; then
  echo "$query_error queries were wrong" >&2
else
  echo "all queries passed"
fi
echo "######"
