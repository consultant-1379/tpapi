#!/bin/bash

if [ "$2" == "" ]; then
  echo usage: $0 \<Module\> \<Branch\> \<Workspace\> [\<UserID\>] [\<D\>]
  exit -1
else
  theDate=\#$(date +"%c")
  module=$1
  branch=$2
  workspace=$3
  install_dir=$workspace/install
  versionProperties=$install_dir/version.properties
  userId=$4
  deliver=$5
  CT=/usr/atria/bin/cleartool
  zipname=TechPackAPI
  releaseArea=/proj/jkadm100/eniq_events_releases
fi

function createJar {

  mkdir $workspace/install
  mkdir $workspace/tmpdir
  cd tmpdir
  /proj/jkadm100/bin/lxb sol10u10sparc jar -xf $workspace/src/build/jython.jar
  /proj/jkadm100/bin/lxb sol10u10sparc jar -xf $workspace/src/build/jconn3.jar
  mkdir TPAPI
  cp $workspace/src/TPAPI/*.py TPAPI
  mkdir Samples
  cp $workspace/src/Samples/*.py Samples
  cd $workspace
  cd $workspace/src/build
  mv jython.jar TPAPI_${rstate}.jar
  cd $workspace
  /proj/jkadm100/bin/lxb sol10u10sparc jar cvmf src/build/Manifest.txt TPAPI_${rstate}.jar -C tmpdir *
  cp TPAPI_${rstate}.jar $workspace/install
  cd $workspace/install

  touch $versionProperties
  echo $theDate >> $versionProperties
  echo module.name=tpapi >> $versionProperties
  echo module.version=$rstate >> $versionProperties
  echo build.tag=b999 >> $versionProperties
  echo author=jkadm100 >> $versionProperties
  echo module.build=999 >> $versionProperties
  echo product.number=$product >> $versionProperties
  echo product.label=$tag_product-$rstate >> $versionProperties
  echo "Zipping all contents of the install directory..."
 
  cd $workspace
  zip -r ${zipname}_$rstate.zip install
  echo "Copying ${zipname}_$rstate.zip to $releaseArea"
  cp ${zipname}_$rstate.zip $releaseArea

}


function getProductNumber {
  product=`cat $workspace/build.cfg | grep $module | grep $branch | awk -F " " '{print $3}'`
  tag_product=`echo $product | sed 's/\//_/g'`
}

function setRstate {

  revision=`cat $workspace/build.cfg | grep $module | grep $branch | awk -F " " '{print $4}'`

  if git tag | grep $product-$revision; then
    rstate=`git tag | grep ${tag_product}-${revision} | tail -1 | sed s/.*-// | perl -nle 'sub nxt{$_=shift;$l=length$_;sprintf"%0${l}d",++$_}print $1.nxt($2) if/^(.*?)(\d+$)/';`
  else
    ammendment_level=01
    rstate=$revision$ammendment_level
  fi

}


function getSprint {
  sprint=`cat $workspace/build.cfg | grep $module | grep $branch | awk -F " " '{print $5}'`
}

getSprint
getProductNumber
setRstate

git clean -df
git checkout $branch
git pull

echo "Building for Sprint:$sprint"
echo "Building UI on $branch"
echo "Building rstate: $rstate"

createJar
rsp=$?

if [ $rsp == 0 ]; then
  git tag $tag_product-$rstate
  git fetch --tags
  git push --tag origin $branch

  echo "Creating temporary rstate file for autodelivery. The file will contain $rstate"
  touch $workspace/rstate.txt
  echo $rstate >> $workspace/rstate.txt
fi

exit $rsp
