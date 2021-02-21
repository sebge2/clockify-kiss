# Clockify Kiss on Snap

Build on: ``ami-007ce78760edefe22 (ubuntu Xenial)``

Install snap:
````
sudo apt update
sudo apt install snapd
sudo snap install snapcraft --classic
````

Setup Git:
````
echo "-----BEGIN OPENSSH PRIVATE KEY-----
-----END OPENSSH PRIVATE KEY-----
" > ~/.ssh/github
echo "" > ~/.ssh/github.pub
chmod 0700 ~/.ssh/github*
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github
git clone git@github.com:sebge2/clockify-kiss.git
````

Build:
````
snapcraft --use-lxd
````

Publish:
````
sudo snap install ./clockify-kiss_1.0.1_amd64.snap --dangerous
snapcraft login
snapcraft push ./clockify-kiss_1.0.1_amd64.snap
snapcraft release clockify-kiss 2 beta
sudo snap install clockify-kiss  --channel=beta
````

Copy config:
````
cp ~/.clockify.cfg ~/snap/clockify-kiss/current/
````
