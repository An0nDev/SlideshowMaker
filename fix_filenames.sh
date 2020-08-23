IFS='
'

for filename in input/*.png; do mv $(printf '%q' "$filename") ${filename/$1/}; done
