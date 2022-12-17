- Test that custom set fields like private_cc_flags and public_cc_flags are not trimmed out when depg is ran again.


Deps Graph: 

dir1/f1 ; deps = []
dir1/f2 ; deps = [dir1/f1]
dir1/main1 ; deps = [dir1/f2]
