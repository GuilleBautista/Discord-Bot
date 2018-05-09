package myBot;

import net.dv8tion.jda.core.entities.Guild;
import net.dv8tion.jda.core.entities.Message;
import net.dv8tion.jda.core.entities.MessageChannel;
import net.dv8tion.jda.core.events.ReadyEvent;
import net.dv8tion.jda.core.events.message.MessageReceivedEvent;
import net.dv8tion.jda.core.hooks.ListenerAdapter;


public class TextListener extends ListenerAdapter{
	
	@Override
	public void onReady(ReadyEvent event) {
		String out="El bot está funcionando en los servidores: \n";
		
		for(Guild g : event.getJDA().getGuilds()) {
			out+="name "+g.getName()+"		id: "+g.getId()+"\n";
			g.getTextChannels().get(0).sendMessage(
					"Hola soy un bot y de momento no hago mucho"
					).queue();
		}
		
		System.out.println(out);
		
	}
	
	    @Override
	    public void onMessageReceived(MessageReceivedEvent event)
	    {
	        if (event.getAuthor().isBot()) return;
	        // We don't want to respond to other bot accounts, including ourself
	        Message message = event.getMessage();
	        String content = message.getContentRaw(); 
	        // getContentRaw() is an atomic getter
	        // getContentDisplay() is a lazy getter which modifies the content for e.g. console view (strip discord formatting)
	        if (content.equalsIgnoreCase("ping")){
	            MessageChannel channel = event.getChannel();
	            channel.sendMessage("Pong!").queue(); // Important to call .queue() on the RestAction returned by sendMessage(...)
	        }
	    }
	   
}
