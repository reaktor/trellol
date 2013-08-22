#!/usr/bin/env ruby
require 'base64'

scale = 5.0
who = Base64.decode64("VmlsaG9uZW46QmlnIGdhaW56")

def love(x, y)
  isLove = x**2 + (((5*y)/4 - Math.sqrt(x.abs))**2)
  isLove >= 0.9 && isLove <= 1.1
end

puts "\n\n"+" "*17 + who.split(":")[0]
(-8..6).each do |x|
  (-20..20).each do |y|
    if love(y/scale/2, -x/scale)
      $stdout.write("*")
    else
      $stdout.write(" ")
    end
  end
  $stdout.write("\n")
end
puts " "*17 + who.split(":")[1] + "\n\n\n"
