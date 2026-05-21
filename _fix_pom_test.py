with open("java-service/pom.xml", "r", encoding="utf-8") as f:
    content = f.read()

# Add H2 test dependency before spring-boot-starter-test
old = """        <!-- === Test === -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>"""

new = """        <!-- === Test === -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>"""

content = content.replace(old, new)
with open("java-service/pom.xml", "w", encoding="utf-8") as f:
    f.write(content)
print("Added JUnit5 + Mockito + H2 + Security Test deps")
