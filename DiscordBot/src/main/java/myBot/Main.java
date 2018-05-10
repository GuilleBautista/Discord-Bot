package myBot;

import net.dv8tion.jda.core.AccountType;
import net.dv8tion.jda.core.JDA;
import net.dv8tion.jda.core.JDABuilder;

public class Main {
	
	public static void main(String[] arguments) throws Exception
	{
	    JDA api = new JDABuilder(AccountType.BOT).setToken("NDMyMzE0MjQ0MjM1NjU3MjM2.DawaBQ.IGtyZHCYmJ6jAUT55vBmoZZfRZA").buildAsync();
	    
	    api.addEventListener(new TextListener());
	    
	    api.addEventListener(new VoiceListener());

	}	

}
